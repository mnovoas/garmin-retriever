# Database schema

`garmin-retriever db` writes a local SQLite database. Tables are created automatically on first ingest; `schema.sql` holds the DDL. There are three kinds of table.

```
          DAILY METRIC TABLES                        INTRADAY TABLES
      (1 row per day, PK = date)                  (many rows per day)
   +----------+ +----------+                     +---------------------+
   | steps    | | sleep    |                     | hr_intraday         |
   | weight   | | hrv      |  ....  date  ....    | body_battery_intra. |
   | stress   | | spo2     |         |            | spo2_intraday       |
   |  ...     | |  ...     |         |            | hrv_intraday        |
   +----------+ +----------+         |            +---------------------+
                                     |
              join on `date` ('YYYY-MM-DD') -------+

   +---------------+
   | activities    |   standalone; PK = activity_id (also carries its own `date`)
   +---------------+
```

`*` marks the primary key. There are no enforced foreign keys (SQLite); tables relate logically through the shared `date` calendar key (`YYYY-MM-DD`). Each intraday table's `date` matches the corresponding daily table's `date`.

## Daily metric tables

One row per calendar day, `date TEXT PRIMARY KEY`. Columns carry normalized units (kg, km, hours, ms, %, L).

```
+--------------------+   +--------------------------+   +-------------------------+
| bodybattery        |   | fitnessage               |   | heartrate               |
+--------------------+   +--------------------------+   +-------------------------+
| * date             |   | * date                   |   | * date                  |
|   charged          |   |   chronological_age      |   |   resting_hr_bpm        |
|   drained          |   |   fitness_age            |   |   min_hr_bpm            |
|   day_min          |   |   achievable_fitness_age |   |   max_hr_bpm            |
|   day_max          |   |   previous_fitness_age   |   |   7_day_avg_resting_bpm |
+--------------------+   +--------------------------+   +-------------------------+

+---------------------------+   +---------------------+   +--------------------------+
| hrv                       |   | hydration           |   | menstrual                |
+---------------------------+   +---------------------+   +--------------------------+
| * date                    |   | * date              |   | * date                   |
|   weekly_avg_ms           |   |   intake_l          |   |   cycle_type             |
|   last_night_avg_ms       |   |   goal_l            |   |   current_phase          |
|   last_night_5min_high_ms |   |   sweat_loss_l      |   |   day_in_cycle           |
|   status                  |   |   activity_intake_l |   |   days_until_next_phase  |
|   baseline_low_ms         |   +---------------------+   |   period_length          |
|   baseline_high_ms        |                             |   predicted_cycle        |
+---------------------------+                             |   predicted_cycle_length |
                                                          |   fertile_window_start   |
                                                          |   luteal_phase_start     |
                                                          +--------------------------+

+----------------------+   +--------------------+   +----------------------+
| nutrition            |   | sleep              |   | spo2                 |
+----------------------+   +--------------------+   +----------------------+
| * date               |   | * date             |   | * date               |
|   calorie_goal_kcal  |   |   sleep_h          |   |   avg_spo2_pct       |
|   adjusted_goal_kcal |   |   deep_h           |   |   lowest_spo2_pct    |
|   meals_logged       |   |   light_h          |   |   latest_spo2_pct    |
+----------------------+   |   rem_h            |   |   avg_sleep_spo2_pct |
                           |   awake_h          |   |   7_day_avg_spo2_pct |
                           |   nap_h            |   +----------------------+
                           |   avg_hr_bpm       |                           
                           |   respiration_brpm |                           
                           |   avg_spo2_pct     |                           
                           |   avg_sleep_stress |                           
                           |   awake_count      |                           
                           |   sleep_score      |                           
                           +--------------------+                           

+--------------------+   +--------------------+   +---------------------+
| steps              |   | stress             |   | usersummary         |
+--------------------+   +--------------------+   +---------------------+
| * date             |   | * date             |   | * date              |
|   steps            |   |   overall_stress   |   |   steps             |
|   distance_km      |   |   rest_h           |   |   distance_km       |
|   step_goal        |   |   low_h            |   |   total_cal_kcal    |
+--------------------+   |   medium_h         |   |   active_cal_kcal   |
                         |   high_h           |   |   bmr_cal_kcal      |
                         +--------------------+   |   resting_hr_bpm    |
                                                  |   min_hr_bpm        |
                                                  |   max_hr_bpm        |
                                                  |   avg_stress        |
                                                  |   max_stress        |
                                                  |   bb_high           |
                                                  |   bb_low            |
                                                  |   bb_charged        |
                                                  |   bb_drained        |
                                                  |   avg_spo2_pct      |
                                                  |   floors_up         |
                                                  |   intensity_min_mod |
                                                  |   intensity_min_vig |
                                                  |   sleeping_h        |
                                                  +---------------------+

+--------------------+   +--------------------+   +--------------------+
| weight             |   | weightgoal         |   | wellnessactivity   |
+--------------------+   +--------------------+   +--------------------+
| * date             |   | * goal_type        |   | * activity_uuid    |
|   weight_kg        |   |   category         |   |   date             |
|   bmi              |   |   name             |   |   name             |
|   body_fat_pct     |   |   goal_value       |   |   type             |
|   body_water_pct   |   |   start_date       |   |   start_local      |
|   bone_mass_kg     |   |   end_date         |   |   end_local        |
|   muscle_mass_kg   |   |   tracking_period  |   |   notes            |
+--------------------+   +--------------------+   +--------------------+

```

## Activities
```
+--------------------+
| activities         |
+--------------------+
| * activity_id      |
|   date             |
|   start_local      |
|   name             |
|   type             |
|   distance_km      |
|   duration_min     |
|   avg_speed_km_h   |
+--------------------+
```

## Intraday tables

Long/narrow time series. `ts` is **epoch milliseconds (UTC)**; HRV uses Garmin's local-time string. Composite primary keys make re-ingests idempotent.

```
+--------------------+   +-----------------------+
| hr_intraday        |   | body_battery_intraday |
+--------------------+   +-----------------------+
| * date TEXT        |   | * date TEXT           |
| * ts INTEGER       |   | * ts INTEGER          |
|   bpm INTEGER      |   |   level INTEGER       |
+--------------------+   +-----------------------+

+-----------------------+   +---------------------------+
| spo2_intraday         |   | hrv_intraday              |
+-----------------------+   +---------------------------+
| * date TEXT           |   | * date TEXT               |
| * ts INTEGER          |   | * reading_time_local TEXT |
|   spo2 INTEGER        |   |   hrv_ms INTEGER          |
|   monitoring_env REAL |   +---------------------------+
+-----------------------+                                

```

## Relationships & conventions

- **Daily tables ⟷ daily tables:** join on `date`, e.g. `SELECT s.date, s.steps, h.resting_hr_bpm FROM steps s JOIN heartrate h USING(date);`
- **Intraday ⟷ daily:** each `*_intraday.date` equals a daily row's `date` (a day has one daily row and many intraday rows).
- **activities:** keyed by `activity_id`; its `date` can be joined to the daily tables.
- **Idempotency:** every write is `INSERT OR REPLACE` on the primary key, so re-running any range updates in place rather than duplicating.
- **Empty tables:** `hydration`, `weightgoal`, `wellnessactivity`, `menstrual` may have no rows if the account has no such data; their columns still exist (from the API spec).
