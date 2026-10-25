"""CLI for garmin-retriever.

Each metric command sends its output to exactly one destination (never both):
  --out FILE   export to a file; the extension sets the format (.csv or .json)
  --db  SQLITE ingest that metric (with its intraday) into a SQLite database
The `db` command ingests all metrics into a database in one run.

Pick the window with --from/--to, --last, or --all (mutually exclusive). --last
takes a number and a unit: d=days, m=months, y=years (e.g. 30d, 3m, 2y), ending
today. --all retrieves everything from the earliest data to today.

Range commands (auto-chunked):
    weight hrv sleep steps stress bodybattery hydration weightgoal
    wellnessactivity activities
    python -m garmin_retriever.cli steps --from 2026-01-01 --to 2026-10-24 --out steps.csv
    python -m garmin_retriever.cli activities --last 1y --out activities.csv
    python -m garmin_retriever.cli steps --all --out steps.csv      # full history
    (weight also has --entries: include every weight entry per day, JSON only)

Single-date commands (one --date, or loop each day of a --from/--to / --last range):
    fitnessage heartrate usersummary spo2 nutrition menstrual
    python -m garmin_retriever.cli usersummary --last 7d --out usersummary.csv

No-date commands (one-shot):
    profile hrzones
    python -m garmin_retriever.cli hrzones --out hrzones.csv

By activity id:
    activity --id N --out activity.json      (full detail)
    workouts --id N --out workouts.json
    download --id N --out activity.zip        (original file)
"""

import argparse
import calendar
import csv
import io
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from .client import GarminClient
from . import tabular
from . import db as dbmod

# Earliest plausible start for --all (before any Garmin wearable data).
EPOCH_START = "2010-01-01"

# Range commands: (client, start, end, args) -> JSON
RANGE_CMDS = {
    "weight": lambda c, s, e, a: c.weight_range(s, e, include_all=a.entries),
    "hrv": lambda c, s, e, a: c.hrv_daily(s, e),
    "sleep": lambda c, s, e, a: c.sleep_summaries(s, e),
    "steps": lambda c, s, e, a: c.steps_daily(s, e),
    "stress": lambda c, s, e, a: c.stress_daily(s, e),
    "bodybattery": lambda c, s, e, a: c.body_battery_daily(s, e),
    "hydration": lambda c, s, e, a: c.hydration_daily(s, e),
    "weightgoal": lambda c, s, e, a: c.weight_goal(s, e),
    "wellnessactivity": lambda c, s, e, a: c.wellness_activities(s, e),
    "activities": lambda c, s, e, a: c.activities(s, e),
}

# Single-calendar-date commands: (client, date) -> JSON
DATE_CMDS = {
    "fitnessage": lambda c, d: c.fitness_age(d),
    "heartrate": lambda c, d: c.daily_heart_rate(d),
    "usersummary": lambda c, d: c.user_summary_daily(d),
    "spo2": lambda c, d: c.spo2_acclimation(d),
    "nutrition": lambda c, d: c.nutrition_log(d),
    "menstrual": lambda c, d: c.menstrual_summary(d),
}

# No-date, one-shot commands: (client) -> JSON
CONFIG_CMDS = {
    "profile": lambda c: c.user_profile_settings(),
    "hrzones": lambda c: c.heart_rate_zones(),
}

# By-activity-id commands: (kind, (client, id) -> data). kind controls output.
ID_CMDS = {
    "activity": ("json", lambda c, i: c.activity(i)),
    "workouts": ("json", lambda c, i: c.activity_workouts(i)),
    "download": ("zip", lambda c, i: c.download_activity(i)),
}


def _iter_dates(start, end):
    cur, end = date.fromisoformat(start), date.fromisoformat(end)
    while cur <= end:
        yield cur.isoformat()
        cur += timedelta(days=1)


def _sub_months(d, months):
    """Subtract whole months from a date, clamping the day to the target month."""
    idx = d.year * 12 + (d.month - 1) - months
    year, month = divmod(idx, 12)
    month += 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _parse_last(spec, parser):
    """Turn '30d' / '3m' / '2y' into (start_iso, end_iso) ending today."""
    m = re.fullmatch(r"(\d+)([dmy])", spec.strip().lower())
    if not m:
        parser.error(f"--last: invalid value {spec!r}; use e.g. 30d, 3m, 2y")
    n, unit = int(m.group(1)), m.group(2)
    end = date.today()
    if unit == "d":
        start = end - timedelta(days=n)
    else:
        start = _sub_months(end, n if unit == "m" else n * 12)
    return start.isoformat(), end.isoformat()


def _resolve_range(args, parser, allow_date):
    """Resolve the requested window to (start, end, single)."""
    has_range = bool(args.start or args.end)
    if args.all:
        if args.last or has_range or (allow_date and args.date):
            parser.error("--all cannot be combined with --date, --last, or --from/--to")
        return EPOCH_START, date.today().isoformat(), False
    if args.last:
        if has_range or (allow_date and args.date):
            parser.error("--last cannot be combined with --date or --from/--to")
        start, end = _parse_last(args.last, parser)
        return start, end, False
    if allow_date and args.date:
        if has_range:
            parser.error("use --date, or --from/--to, not both")
        return args.date, args.date, True
    if args.start and args.end:
        return args.start, args.end, False
    if allow_date:
        parser.error("provide --date, --all, --last, or both --from and --to")
    parser.error("provide --all, --last, or both --from and --to")


def _build_parser():
    parser = argparse.ArgumentParser(prog="garmin-retriever")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p):
        p.add_argument("--last", metavar="Nd|Nm|Ny",
                       help="range ending today, e.g. 30d, 3m, 2y (not with --from/--to)")
        p.add_argument("--all", action="store_true",
                       help="retrieve all available history (earliest data to today)")
        dest = p.add_mutually_exclusive_group(required=True)
        dest.add_argument("--out",
                          help="export to this file; extension sets the format (.csv or .json)")
        dest.add_argument("--db", dest="db_path",
                          help="ingest into this SQLite database instead (never both)")

    for name in RANGE_CMDS:
        p = sub.add_parser(name, help=f"{name} over a date range")
        p.add_argument("--from", dest="start", help="start date YYYY-MM-DD")
        p.add_argument("--to", dest="end", help="end date YYYY-MM-DD")
        if name == "weight":
            p.add_argument("--entries", action="store_true",
                           help="include every weight entry per day (JSON only)")
        add_common(p)

    for name in DATE_CMDS:
        p = sub.add_parser(name, help=f"{name} for a date, or each day in a range")
        p.add_argument("--date", help="single date YYYY-MM-DD")
        p.add_argument("--from", dest="start", help="range start YYYY-MM-DD")
        p.add_argument("--to", dest="end", help="range end YYYY-MM-DD")
        add_common(p)

    for name in CONFIG_CMDS:
        p = sub.add_parser(name, help=f"{name} (one-shot, no date)")
        p.add_argument("--out", required=True,
                       help="output path; extension sets the format (.csv or .json)")

    for name in ID_CMDS:
        p = sub.add_parser(name, help=f"{name} for one activity id")
        p.add_argument("--id", dest="activity_id", required=True, help="activity id")
        p.add_argument("--out", required=True, help="output path (required)")

    dbp = sub.add_parser("db", help="load metrics into a local SQLite database (incl. intraday)")
    dbp.add_argument("--from", dest="start", help="start date YYYY-MM-DD")
    dbp.add_argument("--to", dest="end", help="end date YYYY-MM-DD")
    dbp.add_argument("--last", metavar="Nd|Nm|Ny", help="range ending today, e.g. 30d, 3m, 2y")
    dbp.add_argument("--all", action="store_true", help="all available history (earliest to today)")
    dbp.add_argument("--db", dest="db_path", required=True, help="SQLite database file path")
    dbp.add_argument("--metrics", help="comma-separated subset (default: all)")

    return parser


def _render(command, data, fmt):
    if fmt == "json":
        return json.dumps(data, indent=2)
    headers, rows = tabular.BUILDERS[command](data)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    return buf.getvalue()


def _out_path(args):
    """Resolve the required --out path, creating parent dirs."""
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _format_from_out(args, parser):
    """Derive the output format from the --out file extension."""
    ext = Path(args.out).suffix.lower()
    if ext == ".csv":
        return "csv"
    if ext == ".json":
        return "json"
    parser.error(f"--out: unsupported extension {ext or '(none)'}; use .csv or .json")


def _save(out, payload):
    if isinstance(payload, bytes):
        out.write_bytes(payload)
    else:
        out.write_text(payload)
    print(f"wrote {out}", file=sys.stderr)


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    client = GarminClient()
    cmd = args.command

    if cmd == "db":
        start, end, _ = _resolve_range(args, parser, allow_date=False)
        metrics = ([m.strip() for m in args.metrics.split(",")]
                   if args.metrics else dbmod.ALL_METRICS)
        unknown = [m for m in metrics if m not in dbmod.ALL_METRICS]
        if unknown:
            parser.error(f"unknown metric(s): {', '.join(unknown)}; "
                         f"choose from {', '.join(dbmod.ALL_METRICS)}")
        conn = dbmod.connect(args.db_path)
        summary = dbmod.ingest(conn, client, metrics, start, end,
                               log=lambda m: print(m, file=sys.stderr))
        conn.close()
        for m, v in summary.items():
            extra = f", {v['intraday']} intraday" if "intraday" in v else ""
            print(f"  {m}: {v['daily']} daily{extra}", file=sys.stderr)
        print(f"wrote {args.db_path}", file=sys.stderr)
        return

    if cmd in ID_CMDS:
        kind, fetch = ID_CMDS[cmd]
        data = fetch(client, args.activity_id)
        payload = data if kind == "zip" else json.dumps(data, indent=2)
        _save(_out_path(args), payload)
        return

    if cmd in CONFIG_CMDS:
        data = CONFIG_CMDS[cmd](client)
        _save(_out_path(args), _render(cmd, data, _format_from_out(args, parser)))
        return

    is_date_cmd = cmd in DATE_CMDS
    start, end, single = _resolve_range(args, parser, allow_date=is_date_cmd)

    # Destination: database (one metric) or file -- mutually exclusive, one required.
    if getattr(args, "db_path", None):
        conn = dbmod.connect(args.db_path)
        summary = dbmod.ingest(conn, client, [cmd], start, end,
                               log=lambda m: print(m, file=sys.stderr))
        conn.close()
        v = summary[cmd]
        extra = f", {v['intraday']} intraday" if "intraday" in v else ""
        print(f"wrote {args.db_path}: {cmd} {v['daily']} daily{extra}", file=sys.stderr)
        return

    fmt = _format_from_out(args, parser)
    if cmd in RANGE_CMDS:
        data = RANGE_CMDS[cmd](client, start, end, args)
    elif single:
        data = DATE_CMDS[cmd](client, start)
    else:
        fetch = DATE_CMDS[cmd]
        data = [r for d in _iter_dates(start, end)
                if (r := fetch(client, d)) is not None]

    _save(_out_path(args), _render(cmd, data, fmt))


if __name__ == "__main__":
    main()
