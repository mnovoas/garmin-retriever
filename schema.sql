-- garmin-retriever SQLite schema (reference).
-- Tables are created automatically on first `cli db` ingest; this file documents
-- the layout. Regenerate with: sqlite3 <db> ".schema" after a fresh init_schema().

CREATE TABLE "weight" ("date", "weight_kg", "bmi", "body_fat_pct", "body_water_pct", "bone_mass_kg", "muscle_mass_kg", PRIMARY KEY ("date"));
CREATE TABLE "steps" ("date", "steps", "distance_km", "step_goal", PRIMARY KEY ("date"));
CREATE TABLE "stress" ("date", "overall_stress", "rest_h", "low_h", "medium_h", "high_h", PRIMARY KEY ("date"));
CREATE TABLE "sleep" ("date", "sleep_h", "deep_h", "light_h", "rem_h", "awake_h", "nap_h", "avg_hr_bpm", "respiration_brpm", "avg_spo2_pct", "avg_sleep_stress", "awake_count", "sleep_score", PRIMARY KEY ("date"));
CREATE TABLE "hydration" ("date", "intake_l", "goal_l", "sweat_loss_l", "activity_intake_l", PRIMARY KEY ("date"));
CREATE TABLE "weightgoal" ("goal_type", "category", "name", "goal_value", "start_date", "end_date", "tracking_period", PRIMARY KEY ("goal_type"));
CREATE TABLE "wellnessactivity" ("activity_uuid", "date", "name", "type", "start_local", "end_local", "notes", PRIMARY KEY ("activity_uuid"));
CREATE TABLE "activities" ("activity_id", "date", "start_local", "name", "type", "distance_km", "duration_min", "avg_speed_km_h", PRIMARY KEY ("activity_id"));
CREATE TABLE "fitnessage" ("date", "chronological_age", "fitness_age", "achievable_fitness_age", "previous_fitness_age", PRIMARY KEY ("date"));
CREATE TABLE "usersummary" ("date", "steps", "distance_km", "total_cal_kcal", "active_cal_kcal", "bmr_cal_kcal", "resting_hr_bpm", "min_hr_bpm", "max_hr_bpm", "avg_stress", "max_stress", "bb_high", "bb_low", "bb_charged", "bb_drained", "avg_spo2_pct", "floors_up", "intensity_min_mod", "intensity_min_vig", "sleeping_h", PRIMARY KEY ("date"));
CREATE TABLE "nutrition" ("date", "calorie_goal_kcal", "adjusted_goal_kcal", "meals_logged", PRIMARY KEY ("date"));
CREATE TABLE "menstrual" ("date", "cycle_type", "current_phase", "day_in_cycle", "days_until_next_phase", "period_length", "predicted_cycle", "predicted_cycle_length", "fertile_window_start", "luteal_phase_start", PRIMARY KEY ("date"));
CREATE TABLE "hrv" ("date", "weekly_avg_ms", "last_night_avg_ms", "last_night_5min_high_ms", "status", "baseline_low_ms", "baseline_high_ms", PRIMARY KEY ("date"));
CREATE TABLE "heartrate" ("date", "resting_hr_bpm", "min_hr_bpm", "max_hr_bpm", "7_day_avg_resting_bpm", PRIMARY KEY ("date"));
CREATE TABLE "bodybattery" ("date", "charged", "drained", "day_min", "day_max", PRIMARY KEY ("date"));
CREATE TABLE "spo2" ("date", "avg_spo2_pct", "lowest_spo2_pct", "latest_spo2_pct", "avg_sleep_spo2_pct", "7_day_avg_spo2_pct", PRIMARY KEY ("date"));
CREATE TABLE hr_intraday (date TEXT, ts INTEGER, bpm INTEGER, PRIMARY KEY (date, ts));
CREATE TABLE body_battery_intraday (date TEXT, ts INTEGER, level INTEGER, PRIMARY KEY (date, ts));
CREATE TABLE spo2_intraday (date TEXT, ts INTEGER, spo2 INTEGER, monitoring_env REAL, PRIMARY KEY (date, ts));
CREATE TABLE hrv_intraday (date TEXT, reading_time_local TEXT, hrv_ms INTEGER, PRIMARY KEY (date, reading_time_local));
