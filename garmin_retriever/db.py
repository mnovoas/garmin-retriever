"""Load retrieved Garmin data into a local SQLite database.

Design (see docs/api-reference.md for the API shapes):
  - One daily table per metric, keyed by date, with the same normalized,
    unit-labeled columns as the CSV output (reusing `tabular` flatteners).
    Column names are sanitized (e.g. "weight (kg)" -> "weight_kg").
  - Activities go in their own table keyed by activity id.
  - Intraday series (dropped from the CSVs) go in dedicated long tables:
      hr_intraday(date, ts, bpm)
      body_battery_intraday(date, ts, level)
      spo2_intraday(date, ts, spo2, monitoring_env)
      hrv_intraday(date, reading_time_local, hrv_ms)
  - All writes are INSERT OR REPLACE on the primary key, so re-ingesting a
    range is idempotent.

Data is fetched live from the API (not the CSVs) so the intraday arrays, which
the CSVs drop, are captured. Config endpoints (profile, hrzones) are settings
snapshots, not time series, so they are intentionally not loaded here.
"""

import json
import re
import sqlite3
from datetime import date, timedelta

from . import tabular

# metric -> fetch(client, start, end) returning data in the shape its tabular
# builder expects. Single-date endpoints are looped into a list of day records.
SIMPLE = {
    "weight": lambda c, s, e: c.weight_range(s, e),
    "steps": lambda c, s, e: c.steps_daily(s, e),
    "stress": lambda c, s, e: c.stress_daily(s, e),
    "sleep": lambda c, s, e: c.sleep_summaries(s, e),
    "hydration": lambda c, s, e: c.hydration_daily(s, e),
    "weightgoal": lambda c, s, e: c.weight_goal(s, e),
    "wellnessactivity": lambda c, s, e: c.wellness_activities(s, e),
    "activities": lambda c, s, e: c.activities(s, e),
    "fitnessage": lambda c, s, e: _collect(c.fitness_age, s, e),
    "usersummary": lambda c, s, e: _collect(c.user_summary_daily, s, e),
    "nutrition": lambda c, s, e: _collect(c.nutrition_log, s, e),
    "menstrual": lambda c, s, e: _collect(c.menstrual_summary, s, e),
}

# Metrics with a dedicated ingest (daily + intraday); handled below.
SPECIAL = ["hrv", "heartrate", "bodybattery", "spo2"]

ALL_METRICS = list(SIMPLE) + SPECIAL

# Builders expecting a dict (not a list) as input; used to synthesize empty input.
_DICT_INPUT = {"weight", "hrv", "weightgoal"}

INTRADAY_DDL = {
    "hr_intraday": "CREATE TABLE IF NOT EXISTS hr_intraday "
                   "(date TEXT, ts INTEGER, bpm INTEGER, PRIMARY KEY (date, ts))",
    "body_battery_intraday": "CREATE TABLE IF NOT EXISTS body_battery_intraday "
                             "(date TEXT, ts INTEGER, level INTEGER, PRIMARY KEY (date, ts))",
    "spo2_intraday": "CREATE TABLE IF NOT EXISTS spo2_intraday "
                     "(date TEXT, ts INTEGER, spo2 INTEGER, monitoring_env REAL, PRIMARY KEY (date, ts))",
    "hrv_intraday": "CREATE TABLE IF NOT EXISTS hrv_intraday "
                    "(date TEXT, reading_time_local TEXT, hrv_ms INTEGER, "
                    "PRIMARY KEY (date, reading_time_local))",
}


def connect(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_schema(conn):
    """Create every table with its full column set and no data.

    Daily tables take their columns from the tabular builders (which return fixed
    headers regardless of data), so the schema is complete even for metrics the
    account has no data for."""
    for metric in ALL_METRICS:
        headers, _ = tabular.BUILDERS[metric]({} if metric in _DICT_INPUT else [])
        _create_daily_table(conn, metric, headers)
    for ddl in INTRADAY_DDL.values():
        conn.execute(ddl)
    conn.commit()


def _iter_dates(start, end):
    cur, end = date.fromisoformat(start), date.fromisoformat(end)
    while cur <= end:
        yield cur.isoformat()
        cur += timedelta(days=1)


def _collect(method, start, end):
    """Loop a single-date endpoint over a range, dropping empty days."""
    out = []
    for d in _iter_dates(start, end):
        rec = method(d)
        if rec is not None:
            out.append(rec)
    return out


def _col(header):
    """Sanitize a CSV header into a SQL column name."""
    h = header.lower().replace("%", "pct").replace("/", " ")
    h = re.sub(r"[()]", "", h)
    h = re.sub(r"[^a-z0-9]+", "_", h).strip("_")
    return h or "col"


def _create_daily_table(conn, table, headers):
    """Create a daily table (if needed) from builder headers; first column is PK."""
    cols = [_col(h) for h in headers]
    coldefs = ", ".join(f'"{c}"' for c in cols)
    conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({coldefs}, PRIMARY KEY ("{cols[0]}"))')
    return cols


def _write_daily(conn, table, headers, rows):
    """Create (if needed) a daily table from builder headers and upsert rows."""
    cols = _create_daily_table(conn, table, headers)
    placeholders = ",".join("?" * len(cols))
    collist = ",".join(f'"{c}"' for c in cols)
    conn.executemany(
        f'INSERT OR REPLACE INTO "{table}" ({collist}) VALUES ({placeholders})', rows
    )
    return len(rows)


def _ingest_simple(conn, client, metric, start, end):
    data = SIMPLE[metric](client, start, end)
    headers, rows = tabular.BUILDERS[metric](data)
    return _write_daily(conn, metric, headers, rows)


def _ingest_heartrate(conn, client, start, end):
    conn.execute(INTRADAY_DDL["hr_intraday"])
    records, intraday = [], []
    for d in _iter_dates(start, end):
        rec = client.daily_heart_rate(d)
        if not rec:
            continue
        records.append(rec)
        day = rec.get("calendarDate") or d
        for pair in rec.get("heartRateValues") or []:
            if len(pair) >= 2:
                intraday.append((day, pair[0], pair[1]))
    headers, rows = tabular.heartrate_rows(records)
    n = _write_daily(conn, "heartrate", headers, rows)
    conn.executemany("INSERT OR REPLACE INTO hr_intraday (date, ts, bpm) VALUES (?,?,?)", intraday)
    return n, len(intraday)


def _ingest_spo2(conn, client, start, end):
    conn.execute(INTRADAY_DDL["spo2_intraday"])
    records, intraday = [], []
    for d in _iter_dates(start, end):
        rec = client.spo2_acclimation(d)
        if not rec:
            continue
        records.append(rec)
        day = rec.get("calendarDate") or d
        for row in rec.get("spO2HourlyAverages") or []:
            if len(row) >= 2:
                intraday.append((day, row[0], row[1], row[2] if len(row) > 2 else None))
    headers, rows = tabular.spo2_rows(records)
    n = _write_daily(conn, "spo2", headers, rows)
    conn.executemany(
        "INSERT OR REPLACE INTO spo2_intraday (date, ts, spo2, monitoring_env) VALUES (?,?,?,?)",
        intraday)
    return n, len(intraday)


def _ingest_bodybattery(conn, client, start, end):
    conn.execute(INTRADAY_DDL["body_battery_intraday"])
    data = client.body_battery_daily(start, end)
    intraday = []
    for day in data:
        d = day.get("date")
        for pair in day.get("bodyBatteryValuesArray") or []:
            if len(pair) >= 2:
                intraday.append((d, pair[0], pair[1]))
    headers, rows = tabular.bodybattery_rows(data)
    n = _write_daily(conn, "bodybattery", headers, rows)
    conn.executemany(
        "INSERT OR REPLACE INTO body_battery_intraday (date, ts, level) VALUES (?,?,?)", intraday)
    return n, len(intraday)


def _ingest_hrv(conn, client, start, end):
    conn.execute(INTRADAY_DDL["hrv_intraday"])
    daily = client.hrv_daily(start, end)
    headers, rows = tabular.hrv_rows(daily)
    n = _write_daily(conn, "hrv", headers, rows)
    intraday = []
    for d in _iter_dates(start, end):
        rec = client.hrv(d)
        if not rec:
            continue
        day = (rec.get("hrvSummary") or {}).get("calendarDate") or d
        for r in rec.get("hrvReadings") or []:
            intraday.append((day, r.get("readingTimeLocal"), r.get("hrvValue")))
    conn.executemany(
        "INSERT OR REPLACE INTO hrv_intraday (date, reading_time_local, hrv_ms) VALUES (?,?,?)",
        intraday)
    return n, len(intraday)


_SPECIAL_FN = {
    "heartrate": _ingest_heartrate,
    "spo2": _ingest_spo2,
    "bodybattery": _ingest_bodybattery,
    "hrv": _ingest_hrv,
}


def ingest(conn, client, metrics, start, end, log=None):
    """Ingest the given metrics for [start, end] into conn. Returns a summary dict."""
    summary = {}
    for metric in metrics:
        if log:
            log(f"ingesting {metric} ...")
        if metric in _SPECIAL_FN:
            daily_n, intraday_n = _SPECIAL_FN[metric](conn, client, start, end)
            summary[metric] = {"daily": daily_n, "intraday": intraday_n}
        else:
            summary[metric] = {"daily": _ingest_simple(conn, client, metric, start, end)}
        conn.commit()
    return summary
