# garmin-retriever

Retrieve **your own** Garmin Connect data via the [Garmin Connect **Personal API**](https://developer.garmin.com/gc-developer-program/personal/) and export it to CSV/JSON files or load it into a local SQLite database — including intraday time series.

> Unofficial. Not affiliated with or endorsed by Garmin. It only accesses the data of the account whose Personal API key you provide, and all endpoints are read-only.

## Features

- **25 Personal API endpoints** — weight, sleep, HRV, steps, stress, Body Battery, SpO2, heart rate, fitness age, daily summaries, nutrition, hydration, activities, and more.
- **CSV or JSON output**, chosen by file extension; CSV columns are normalized with units in the header (`weight (kg)`, `sleep (h)`, `distance (km)`, …).
- **Flexible date windows**: `--from/--to`, `--last 30d|3m|2y`, or `--all` (full history).
- **Local SQLite database** with one table per metric plus dedicated **intraday** tables (per-minute heart rate, Body Battery, SpO2, HRV readings). Re-ingesting is idempotent.
- A single run writes to **either a file or the database, never both**.

## Requirements

- Python **3.9+** built against a modern OpenSSL.
  - On macOS, the system `python3` (3.9, LibreSSL) **fails the TLS handshake** with Garmin. Use Homebrew Python instead: `brew install python` and create the venv with `/opt/homebrew/bin/python3`.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install .            # or: pip install -e .  for development
```

This installs the `garmin-retriever` command.

## Authentication

1. Log in to Garmin Connect on the web, open the **Personal API Key** page, and create a key (it's shown only once).
2. Make the key available in any of these (checked in order):
   - the `GARMIN_PERSONAL_API_KEY` environment variable (a local `.env` works — see `.env.example`),
   - `./connect-personal-api-key`,
   - `~/.config/garmin/connect-personal-api-key`.

The key is exchanged for a short-lived bearer token automatically; the token is cached in memory and re-minted on expiry.

## Usage

Every data command picks a date window and one destination.

```bash
# Export to a file (format from the extension)
garmin-retriever steps --last 30d --out steps.csv
garmin-retriever sleep --from 2026-01-01 --to 2026-06-30 --out sleep.json

# Full history
garmin-retriever weight --all --out weight.csv

# A single day, or loop a range, for single-date endpoints
garmin-retriever heartrate --date 2026-10-22 --out hr.csv
garmin-retriever usersummary --last 7d --out summary.csv

# One-shot config (no date)
garmin-retriever profile --out profile.csv
garmin-retriever hrzones --out zones.csv

# Search your activities in a window (the CSV lists each activity's id)
garmin-retriever activities --last 1y --out activities.csv

# By activity id (use an id from the activities search above)
garmin-retriever activity  --id 24844618907 --out activity.json
garmin-retriever download  --id 24844618907 --out activity.zip   # original file

# Load into SQLite instead of a file (one metric)
garmin-retriever steps --last 1y --db garmin.sqlite

# Load everything (all metrics + intraday) in one run
garmin-retriever db --last 1y --db garmin.sqlite
```

Date window options (mutually exclusive): `--from/--to`, `--last Nd|Nm|Ny`, `--all`. Single-date commands also accept `--date`.

### Commands

| Group | Commands |
|---|---|
| Range metrics | `weight` `steps` `stress` `sleep` `hrv` `bodybattery` `hydration` `weightgoal` `wellnessactivity` `activities` |
| Single-date metrics | `fitnessage` `heartrate` `usersummary` `spo2` `nutrition` `menstrual` |
| Config (no date) | `profile` `hrzones` |
| By activity id | `activity` `workouts` `download` |
| Bulk DB load | `db` |

## Database

The `db` command creates a SQLite database with:

- one **daily table per metric**, keyed by `date`, with the same normalized columns as the CSVs;
- an **`activities`** table keyed by `activity_id`;
- **intraday** tables: `hr_intraday`, `body_battery_intraday`, `spo2_intraday`, `hrv_intraday`.

Tables are created automatically on first ingest; `schema.sql` documents the full layout. All writes are `INSERT OR REPLACE` on the primary key, so re-running a range never duplicates rows.

Query it with any SQLite tool, e.g.:

```bash
sqlite3 -header -column garmin.sqlite \
  "SELECT date, steps, distance_km FROM steps ORDER BY date DESC LIMIT 7;"
# intraday timestamps are epoch-milliseconds UTC:
sqlite3 garmin.sqlite \
  "SELECT datetime(ts/1000,'unixepoch') AS utc, bpm FROM hr_intraday WHERE bpm IS NOT NULL LIMIT 5;"
```

See [DATABASE.md](DATABASE.md) for the full schema diagram.

### Beyond querying

Because it's a plain SQLite file, the database drops into most of the data ecosystem:

- **Grafana dashboards** — add the [`frser-sqlite-datasource`](https://github.com/fr-ser/grafana-sqlite-datasource) plugin, point it at `garmin.sqlite`, and chart resting HR, sleep, Body Battery, steps, etc. The `*_intraday` tables (epoch-ms `ts`) plot directly as time series.
- **Metabase / Redash** — connect SQLite directly for point-and-click dashboards and scheduled reports.
- **pandas / Jupyter** — `pandas.read_sql("SELECT * FROM sleep", sqlite3.connect("garmin.sqlite"))` for notebooks and plots.
- **DuckDB** — `duckdb.sql("SELECT * FROM sqlite_scan('garmin.sqlite','hr_intraday')")` for fast analytics, or export to Parquet.
- Keep a **cron job** running `garmin-retriever db --last 7d --db garmin.sqlite` to incrementally refresh (idempotent upserts), feeding a live dashboard.

## Notes

- **Units** are normalized and labeled in CSV headers / column names: weight & body composition in **kg**, distances in **km**, durations in **hours**, HRV in **ms**, hydration in **L**.
- **`weight/all` is broken** on the live gateway (returns `400`); `weight`/`weight_range` uses the working `weight/range` endpoint.
- **Rate limits** aren't documented; the client is sequential with retry/backoff. Full-history pulls of per-day endpoints (heart rate, SpO2, HRV, usersummary, …) make one request per day and can take a while.
- The API/`docs/api-reference.md` describe the endpoints; `openapi/garmin-personal-api.openapi.json` is the full spec.

## Reference

- [ENDPOINTS.md](ENDPOINTS.md) — every endpoint, its parameters, and response structure.
- [DATABASE.md](DATABASE.md) — SQLite schema diagram and relationships.
- `openapi/garmin-personal-api.openapi.json` — the full OpenAPI spec.

## License

[GNU General Public License v3.0 or later](LICENSE) (GPL-3.0-or-later).
