"""HTTP client for the Garmin Connect Personal API.

Handles token minting/caching/refresh, attaches the bearer header, and retries
transient failures. All endpoints are read-only GETs.
"""

import time
from datetime import date, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import auth

BASE_URL = "https://personal.connectapi.garmin.com"
TIMEOUT = 30  # seconds
EXPIRY_SKEW = 60  # re-mint this many seconds before the JWT's exp

# Max inclusive span each range endpoint accepts; longer ranges are chunked.
STEPS_MAX_DAYS = 28
STRESS_MAX_DAYS = 28
SLEEP_SUMMARY_MAX_DAYS = 31
BODY_BATTERY_MAX_DAYS = 31
HRV_DAILY_MAX_DAYS = 28  # no documented cap; chunk conservatively


def _fmt_date(value):
    """Normalize a date to an ISO YYYY-MM-DD string."""
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _parse_date(value):
    """Coerce a date or ISO string to a datetime.date."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _date_windows(start, end, max_days):
    """Yield (window_start, window_end) date pairs covering [start, end]
    inclusively, each spanning at most max_days days."""
    start = _parse_date(start)
    end = _parse_date(end)
    if end < start:
        raise ValueError(f"end date {end} is before start date {start}")
    step = timedelta(days=max_days - 1)
    cur = start
    while cur <= end:
        window_end = min(cur + step, end)
        yield cur, window_end
        cur = window_end + timedelta(days=1)


def _json(resp):
    """Parse a response body, returning None for 204 / empty bodies."""
    if resp.status_code == 204 or not resp.text.strip():
        return None
    return resp.json()


class GarminClient:
    def __init__(self, api_key=None):
        self._api_key = api_key
        self._token = None
        self._exp = None  # unix seconds, or None if unknown
        self.session = requests.Session()
        retry = Retry(
            total=4,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            respect_retry_after_header=True,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    # -- auth -------------------------------------------------------------
    def _ensure_token(self, force=False):
        now = time.time()
        expired = self._exp is not None and now >= self._exp - EXPIRY_SKEW
        if force or self._token is None or expired:
            self._token, self._exp = auth.mint_token(self._api_key, session=self.session)
        return self._token

    # -- core GET ---------------------------------------------------------
    def get(self, path, params=None):
        """GET a path (relative to BASE_URL) with the bearer token.

        Re-mints the token once on a 401, then surfaces HTTP errors with a body
        snippet for diagnosis.
        """
        url = BASE_URL + path
        token = self._ensure_token()
        resp = self.session.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=TIMEOUT,
        )
        if resp.status_code == 401:
            token = self._ensure_token(force=True)
            resp = self.session.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                timeout=TIMEOUT,
            )
        if resp.status_code // 100 != 2:
            raise requests.HTTPError(
                f"GET {path} -> HTTP {resp.status_code}: {resp.text[:500]}",
                response=resp,
            )
        return resp

    # -- endpoints --------------------------------------------------------
    def weight_range(self, start_date, end_date, include_all=False):
        """GET /weight-service/weight/range/{startDate}/{endDate}.

        Returns a WeightRangeDTO for the inclusive date range:
          - `dailyWeightSummaries`: per day, the `latestWeight`, min/max, entry
            count, and -- when include_all=True -- every entry in
            `allWeightMetrics`;
          - `totalAverage`, `previousDateWeight`, `nextDateWeight`.
        Weights are in grams. Dates may be `datetime.date` or ISO `YYYY-MM-DD`.

        Note: the spec also lists `/weight-service/weight/all/{start}/{end}`, but
        that endpoint returns HTTP 400 on the live gateway (see
        docs/api-reference.md). This is the working equivalent -- use
        include_all=True to get all entries, which is what `weight/all` promised.
        """
        path = f"/weight-service/weight/range/{_fmt_date(start_date)}/{_fmt_date(end_date)}"
        params = {"includeAll": "true"} if include_all else None
        return self.get(path, params=params).json()

    def _range_list(self, start_date, end_date, max_days, build):
        """Fetch a list-returning range endpoint, chunking to max_days and
        concatenating the per-window lists. `build(ws, we)` returns (path, params)."""
        out = []
        for ws, we in _date_windows(start_date, end_date, max_days):
            path, params = build(ws, we)
            out.extend(_json(self.get(path, params=params)) or [])
        return out

    # -- health stats: single calendar date ------------------------------
    def fitness_age(self, calendar_date, full_history_scan=None):
        """GET /fitnessage-service/fitnessage/v2/{calendarDate}.

        Latest Fitness Age as of the date (chronological vs. fitness age,
        achievable age, components)."""
        params = None
        if full_history_scan is not None:
            params = {"fullHistoryScan": str(bool(full_history_scan)).lower()}
        return _json(self.get(f"/fitnessage-service/fitnessage/v2/{_fmt_date(calendar_date)}", params))

    def hrv(self, calendar_date):
        """GET /hrv-service/hrv/{calendarDate}.

        Detailed HRV for one date (`hrvSummary` + per-reading `hrvReadings`).
        Returns None when there is no data (HTTP 204)."""
        return _json(self.get(f"/hrv-service/hrv/{_fmt_date(calendar_date)}"))

    def daily_sleep(self, calendar_date):
        """GET /sleep-service/sleep/dailySleep?date=... — detailed sleep for one date."""
        return _json(self.get("/sleep-service/sleep/dailySleep", {"date": _fmt_date(calendar_date)}))

    def daily_heart_rate(self, calendar_date):
        """GET /wellness-service/wellness/dailyHeartRate?date=... — daily HR
        (resting/min/max + intraday `heartRateValues`)."""
        return _json(self.get("/wellness-service/wellness/dailyHeartRate", {"date": _fmt_date(calendar_date)}))

    # -- health stats: date ranges (auto-chunked) ------------------------
    def steps_daily(self, start_date, end_date):
        """GET /usersummary-service/stats/steps/daily/{s}/{e} — list of daily steps."""
        return self._range_list(
            start_date, end_date, STEPS_MAX_DAYS,
            lambda ws, we: (f"/usersummary-service/stats/steps/daily/{_fmt_date(ws)}/{_fmt_date(we)}", None),
        )

    def stress_daily(self, start_date, end_date):
        """GET /usersummary-service/stats/stress/daily/{s}/{e} — list of daily stress."""
        return self._range_list(
            start_date, end_date, STRESS_MAX_DAYS,
            lambda ws, we: (f"/usersummary-service/stats/stress/daily/{_fmt_date(ws)}/{_fmt_date(we)}", None),
        )

    def sleep_summaries(self, start_date, end_date):
        """GET /sleep-service/sleep/dailySleepSummariesByDate — list of daily sleep summaries."""
        return self._range_list(
            start_date, end_date, SLEEP_SUMMARY_MAX_DAYS,
            lambda ws, we: ("/sleep-service/sleep/dailySleepSummariesByDate",
                            {"startDate": _fmt_date(ws), "endDate": _fmt_date(we)}),
        )

    def body_battery_daily(self, start_date, end_date):
        """GET /wellness-service/wellness/bodyBattery/reports/daily — list of daily Body Battery reports."""
        return self._range_list(
            start_date, end_date, BODY_BATTERY_MAX_DAYS,
            lambda ws, we: ("/wellness-service/wellness/bodyBattery/reports/daily",
                            {"startDate": _fmt_date(ws), "endDate": _fmt_date(we)}),
        )

    def hrv_daily(self, start_date, end_date):
        """GET /hrv-service/hrv/daily/{from}/{to} — daily HRV summaries over a range.

        Returns {"userProfilePk", "hrvSummaries": [...]} with summaries
        concatenated across chunks."""
        summaries = []
        profile = None
        for ws, we in _date_windows(start_date, end_date, HRV_DAILY_MAX_DAYS):
            data = _json(self.get(f"/hrv-service/hrv/daily/{_fmt_date(ws)}/{_fmt_date(we)}")) or {}
            summaries.extend(data.get("hrvSummaries") or [])
            if data.get("userProfilePk") is not None:
                profile = data["userProfilePk"]
        return {"userProfilePk": profile, "hrvSummaries": summaries}

    def hydration_daily(self, start_date, end_date):
        """GET /usersummary-service/stats/hydration/daily/{s}/{e} — daily hydration."""
        return self._range_list(
            start_date, end_date, 31,
            lambda ws, we: (f"/usersummary-service/stats/hydration/daily/{_fmt_date(ws)}/{_fmt_date(we)}", None),
        )

    def daily_summaries_v2(self, start_date, end_date):
        """GET /usersummary-service/v2/dailysummaries — nested daily summaries (chunked 1y)."""
        out = []
        for ws, we in _date_windows(start_date, end_date, 365):
            d = _json(self.get("/usersummary-service/v2/dailysummaries",
                               {"startDate": _fmt_date(ws), "endDate": _fmt_date(we)})) or {}
            out.extend(d.get("data") or [])
        return out

    def wellness_activities(self, start_date, end_date):
        """GET /wellnessactivity-service/activity/summary/range/{from}/{until} — list."""
        path = f"/wellnessactivity-service/activity/summary/range/{_fmt_date(start_date)}/{_fmt_date(end_date)}"
        return _json(self.get(path)) or []

    def weight_goal(self, start_date, end_date):
        """GET /goal-service/goal/user/effective/weightgoal/{s}/{e} — effective weight goals."""
        path = f"/goal-service/goal/user/effective/weightgoal/{_fmt_date(start_date)}/{_fmt_date(end_date)}"
        return _json(self.get(path)) or {}

    def activities(self, start_date, end_date, page_size=100):
        """GET /activitylist-service/activities/search/activities — activities in range,
        auto-paginated (offset start / limit)."""
        out = []
        offset = 0
        while True:
            batch = _json(self.get(
                "/activitylist-service/activities/search/activities",
                {"startDate": _fmt_date(start_date), "endDate": _fmt_date(end_date),
                 "start": offset, "limit": page_size},
            )) or []
            out.extend(batch)
            if len(batch) < page_size:
                return out
            offset += page_size

    # -- single calendar date (rich) -------------------------------------
    def user_summary_daily(self, calendar_date):
        """GET /usersummary-service/usersummary/daily?calendarDate=... — flat daily summary."""
        return _json(self.get("/usersummary-service/usersummary/daily",
                              {"calendarDate": _fmt_date(calendar_date)}))

    def spo2_acclimation(self, calendar_date):
        """GET /wellness-service/wellness/daily/spo2acclimation/{date}."""
        return _json(self.get(f"/wellness-service/wellness/daily/spo2acclimation/{_fmt_date(calendar_date)}"))

    def nutrition_log(self, calendar_date, include_nutrition=True, include_goals=True):
        """GET /nutrition-service/food/logs/{date} — daily nutrition summary."""
        params = {"includeNutrition": str(bool(include_nutrition)).lower(),
                  "includeGoals": str(bool(include_goals)).lower()}
        return _json(self.get(f"/nutrition-service/food/logs/{_fmt_date(calendar_date)}", params))

    def menstrual_summary(self, calendar_date):
        """GET /periodichealth-service/menstrualcycle/summary/{date} (204 -> None).

        The payload has no date field, so the queried date is stamped on it."""
        data = _json(self.get(f"/periodichealth-service/menstrualcycle/summary/{_fmt_date(calendar_date)}"))
        if isinstance(data, dict):
            data.setdefault("calendarDate", _fmt_date(calendar_date))
        return data

    def menstrual_dayview(self, calendar_date):
        """GET /periodichealth-service/menstrualcycle/dayview/{date} (204 -> None)."""
        data = _json(self.get(f"/periodichealth-service/menstrualcycle/dayview/{_fmt_date(calendar_date)}"))
        if isinstance(data, dict):
            data.setdefault("calendarDate", _fmt_date(calendar_date))
        return data

    # -- no date (config) ------------------------------------------------
    def user_profile_settings(self):
        """GET /userprofile-service/userprofile/settings."""
        return _json(self.get("/userprofile-service/userprofile/settings"))

    def heart_rate_zones(self, generate_defaults=None):
        """GET /biometric-service/heartRateZones/v2 — list of HR zone configs."""
        params = None
        if generate_defaults is not None:
            params = {"generateDefaults": str(bool(generate_defaults)).lower()}
        return _json(self.get("/biometric-service/heartRateZones/v2", params)) or []

    # -- by activity id --------------------------------------------------
    def activity(self, activity_id):
        """GET /activity-service/activity/{activityId} — full activity detail."""
        return _json(self.get(f"/activity-service/activity/{activity_id}"))

    def activity_workouts(self, activity_id):
        """GET /activity-service/activity/{activityId}/workouts."""
        return _json(self.get(f"/activity-service/activity/{activity_id}/workouts")) or []

    def download_activity(self, activity_id):
        """GET /download-service/files/activity/{activityId} — original file as zip bytes."""
        return self.get(f"/download-service/files/activity/{activity_id}").content
