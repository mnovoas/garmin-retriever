"""Flatten Personal API responses into CSV rows with normalized, unit-labeled headers.

Each builder takes the parsed JSON from the matching GarminClient method and
returns (headers, rows). Units are normalized here and named in the header
(e.g. weight (kg), sleep (h)); durations are seconds -> hours, masses grams ->
kg, distances meters -> km.
"""


def _kg(grams):
    return None if grams is None else round(grams / 1000, 2)


def _km(meters):
    return None if meters is None else round(meters / 1000, 2)


def _h(seconds):
    return None if seconds is None else round(seconds / 3600, 2)


def _r(value, ndigits=1):
    return None if value is None else round(value, ndigits)


def _as_list(data):
    """Normalize a single-date response (dict) or a looped range (list) to a list."""
    if isinstance(data, list):
        return data
    return [data] if data else []


def weight_rows(data):
    headers = ["date", "weight (kg)", "bmi", "body fat (%)", "body water (%)",
               "bone mass (kg)", "muscle mass (kg)"]
    rows = []
    for day in data.get("dailyWeightSummaries", []):
        lw = day.get("latestWeight") or {}
        rows.append([
            day.get("summaryDate"),
            _kg(lw.get("weight")),
            _r(lw.get("bmi"), 1),
            lw.get("bodyFat"),
            lw.get("bodyWater"),
            _kg(lw.get("boneMass")),
            _kg(lw.get("muscleMass")),
        ])
    return headers, rows


def steps_rows(data):
    headers = ["date", "steps", "distance (km)", "step goal"]
    rows = [[d.get("calendarDate"), d.get("totalSteps"), _km(d.get("totalDistance")),
             d.get("stepGoal")] for d in data]
    return headers, rows


def stress_rows(data):
    headers = ["date", "overall stress", "rest (h)", "low (h)", "medium (h)", "high (h)"]
    rows = []
    for d in data:
        v = d.get("values") or {}
        rows.append([
            d.get("calendarDate"),
            v.get("overallStressLevel"),
            _h(v.get("restStressDuration")),
            _h(v.get("lowStressDuration")),
            _h(v.get("mediumStressDuration")),
            _h(v.get("highStressDuration")),
        ])
    return headers, rows


def sleep_rows(data):
    headers = ["date", "sleep (h)", "deep (h)", "light (h)", "rem (h)", "awake (h)",
               "nap (h)", "avg hr (bpm)", "respiration (brpm)", "avg spo2 (%)",
               "avg sleep stress", "awake count", "sleep score"]
    rows = []
    for d in data:
        overall = (d.get("sleepScores") or {}).get("overall") or {}
        rows.append([
            d.get("calendarDate"),
            _h(d.get("sleepTimeSeconds")),
            _h(d.get("deepSleepSeconds")),
            _h(d.get("lightSleepSeconds")),
            _h(d.get("remSleepSeconds")),
            _h(d.get("awakeSleepSeconds")),
            _h(d.get("napTimeSeconds")),
            d.get("avgHeartRate"),
            d.get("averageRespirationValue"),
            d.get("averageSpO2Value"),
            d.get("avgSleepStress"),
            d.get("awakeCount"),
            overall.get("value"),
        ])
    return headers, rows


def hrv_rows(data):
    headers = ["date", "weekly avg (ms)", "last night avg (ms)", "last night 5min high (ms)",
               "status", "baseline low (ms)", "baseline high (ms)"]
    rows = []
    for d in data.get("hrvSummaries", []):
        b = d.get("baseline") or {}
        rows.append([
            d.get("calendarDate"),
            d.get("weeklyAvg"),
            d.get("lastNightAvg"),
            d.get("lastNight5MinHigh"),
            d.get("status"),
            b.get("balancedLow"),
            b.get("balancedUpper"),
        ])
    return headers, rows


def bodybattery_rows(data):
    headers = ["date", "charged", "drained", "day min", "day max"]
    rows = []
    for d in data:
        levels = [p[1] for p in (d.get("bodyBatteryValuesArray") or [])
                  if len(p) > 1 and p[1] is not None]
        rows.append([
            d.get("date"),
            d.get("charged"),
            d.get("drained"),
            min(levels) if levels else None,
            max(levels) if levels else None,
        ])
    return headers, rows


def fitnessage_rows(data):
    headers = ["date", "chronological age", "fitness age", "achievable fitness age",
               "previous fitness age"]
    rows = []
    for d in _as_list(data):
        rows.append([
            (d.get("lastUpdated") or "")[:10],
            d.get("chronologicalAge"),
            _r(d.get("fitnessAge"), 1),
            _r(d.get("achievableFitnessAge"), 1),
            _r(d.get("previousFitnessAge"), 1),
        ])
    return headers, rows


def heartrate_rows(data):
    headers = ["date", "resting hr (bpm)", "min hr (bpm)", "max hr (bpm)",
               "7-day avg resting (bpm)"]
    rows = []
    for d in _as_list(data):
        rows.append([
            d.get("calendarDate"),
            d.get("restingHeartRate"),
            d.get("minHeartRate"),
            d.get("maxHeartRate"),
            d.get("lastSevenDaysAvgRestingHeartRate"),
        ])
    return headers, rows


def _l(ml):
    """Millilitres -> litres."""
    return None if ml is None else round(ml / 1000, 2)


def hydration_rows(data):
    headers = ["date", "intake (L)", "goal (L)", "sweat loss (L)", "activity intake (L)"]
    rows = [[d.get("calendarDate"), _l(d.get("valueInML")), _l(d.get("goalInML")),
             _l(d.get("sweatLossInML")), _l(d.get("activityIntakeInML"))] for d in data]
    return headers, rows


def weightgoal_rows(data):
    headers = ["goal type", "category", "name", "goal value", "start date", "end date",
               "tracking period"]
    rows = []
    for g in (data or {}).get("userGoals") or []:
        rows.append([
            g.get("userGoalType"), g.get("userGoalCategory"), g.get("goalName"),
            g.get("goalValue"), g.get("startDate"), g.get("endDate"),
            g.get("trackingPeriodType"),
        ])
    return headers, rows


def wellnessactivity_rows(data):
    headers = ["activity uuid", "date", "name", "type", "start (local)", "end (local)", "notes"]
    rows = []
    for a in data:
        rows.append([
            a.get("activityUuid"), a.get("calendarDate"), a.get("activityName"),
            a.get("wellnessActivityType"), a.get("startTimestampLocal"),
            a.get("endTimestampLocal"), a.get("notes"),
        ])
    return headers, rows


def menstrual_rows(data):
    headers = ["date", "cycle type", "current phase", "day in cycle", "days until next phase",
               "period length", "predicted cycle", "predicted cycle length",
               "fertile window start", "luteal phase start"]
    rows = []
    for d in _as_list(data):
        rows.append([
            d.get("calendarDate"), d.get("cycleType"), d.get("currentPhase"),
            d.get("dayInCycle"), d.get("daysUntilNextPhase"), d.get("periodLength"),
            d.get("predictedCycle"), d.get("predictedCycleLength"),
            d.get("fertileWindowStart"), d.get("lutealPhaseStart"),
        ])
    return headers, rows


def usersummary_rows(data):
    headers = ["date", "steps", "distance (km)", "total cal (kcal)", "active cal (kcal)",
               "bmr cal (kcal)", "resting hr (bpm)", "min hr (bpm)", "max hr (bpm)",
               "avg stress", "max stress", "bb high", "bb low", "bb charged", "bb drained",
               "avg spo2 (%)", "floors up", "intensity min (mod)", "intensity min (vig)",
               "sleeping (h)"]
    rows = []
    for d in _as_list(data):
        rows.append([
            d.get("calendarDate"), d.get("totalSteps"), _km(d.get("totalDistanceMeters")),
            d.get("totalKilocalories"), d.get("activeKilocalories"), d.get("bmrKilocalories"),
            d.get("restingHeartRate"), d.get("minHeartRate"), d.get("maxHeartRate"),
            d.get("averageStressLevel"), d.get("maxStressLevel"),
            d.get("bodyBatteryHighestValue"), d.get("bodyBatteryLowestValue"),
            d.get("bodyBatteryChargedValue"), d.get("bodyBatteryDrainedValue"),
            d.get("averageSpo2"), d.get("floorsAscended"),
            d.get("moderateIntensityMinutes"), d.get("vigorousIntensityMinutes"),
            _h(d.get("sleepingSeconds")),
        ])
    return headers, rows


def spo2_rows(data):
    headers = ["date", "avg spo2 (%)", "lowest spo2 (%)", "latest spo2 (%)",
               "avg sleep spo2 (%)", "7-day avg spo2 (%)"]
    rows = []
    for d in _as_list(data):
        rows.append([
            d.get("calendarDate"), d.get("averageSpO2"), d.get("lowestSpO2"),
            d.get("latestSpO2"), d.get("avgSleepSpO2"), _r(d.get("lastSevenDaysAvgSpO2"), 1),
        ])
    return headers, rows


def nutrition_rows(data):
    headers = ["date", "calorie goal (kcal)", "adjusted goal (kcal)", "meals logged"]
    rows = []
    for d in _as_list(data):
        g = d.get("dailyNutritionGoals") or {}
        rows.append([
            d.get("mealDate"), g.get("calories"), g.get("adjustedCalories"),
            len(d.get("mealDetails") or []),
        ])
    return headers, rows


def profile_rows(data):
    headers = ["setting", "value"]
    rows = [[k, v] for k, v in (data or {}).items() if not isinstance(v, (dict, list))]
    return headers, rows


def hrzones_rows(data):
    headers = ["sport", "training method", "max hr used (bpm)", "lactate threshold hr (bpm)",
               "zone1 floor (bpm)", "zone2 floor (bpm)", "zone3 floor (bpm)",
               "zone4 floor (bpm)", "zone5 floor (bpm)"]
    rows = []
    for z in (data if isinstance(data, list) else [data] if data else []):
        rows.append([
            z.get("sport"), z.get("trainingMethod"), z.get("maxHeartRateUsed"),
            z.get("lactateThresholdHeartRateUsed"),
            z.get("zone1Floor"), z.get("zone2Floor"), z.get("zone3Floor"),
            z.get("zone4Floor"), z.get("zone5Floor"),
        ])
    return headers, rows


def activities_rows(data):
    headers = ["activity id", "date", "start (local)", "name", "type",
               "distance (km)", "duration (min)", "avg speed (km/h)"]
    rows = []
    for a in data:
        stl = a.get("startTimeLocal") or ""
        dur = a.get("duration")
        spd = a.get("averageSpeed")
        rows.append([
            a.get("activityId"), stl[:10], stl, a.get("activityName"),
            (a.get("activityType") or {}).get("typeKey"),
            _km(a.get("distance")),
            round(dur / 60, 1) if dur is not None else None,
            round(spd * 3.6, 2) if spd is not None else None,
        ])
    return headers, rows


BUILDERS = {
    "weight": weight_rows,
    "steps": steps_rows,
    "stress": stress_rows,
    "sleep": sleep_rows,
    "hrv": hrv_rows,
    "bodybattery": bodybattery_rows,
    "fitnessage": fitnessage_rows,
    "heartrate": heartrate_rows,
    "usersummary": usersummary_rows,
    "spo2": spo2_rows,
    "nutrition": nutrition_rows,
    "menstrual": menstrual_rows,
    "hydration": hydration_rows,
    "wellnessactivity": wellnessactivity_rows,
    "weightgoal": weightgoal_rows,
    "activities": activities_rows,
    "profile": profile_rows,
    "hrzones": hrzones_rows,
}
