# Garmin Connect Personal API — Reference

Source of truth: `openapi/garmin-personal-api.openapi.json` (OpenAPI 3.0.1, title "Garmin Connect
Personal API" v1.0.0), extracted from the official Swagger docs at
<https://developer.garmin.com/gc-developer-program/personal/swagger-docs/>.

- **Base URL (data + token):** `https://personal.connectapi.garmin.com`
- **Scope:** every endpoint is a **read-only `GET`**. There is nothing to write, so this is purely a
  retrieval surface — a good match for this project.
- **Access:** the Personal API returns **only the authenticated user's own data**.

## Authentication

The OpenAPI file declares **no** `securitySchemes`, so the flow below is documented from the
overview page and **confirmed live** on 2026-10-24.

1. **Create a Personal API key** (one-time, in a browser): Garmin Connect web account → Personal API
   Key page → *Create Key* → accept T&Cs → choose expiration → *Create*. **The key is shown once** —
   store it like a password. (It currently lives on disk at `./connect-personal-api-key` and
   `~/.config/garmin/connect-personal-api-key` — gitignored.)
2. **Exchange the key for an access token:**
   ```
   POST https://personal.connectapi.garmin.com/personalapitoken-service/personal-api/personal-api-key/token
   Authorization: ApiKey <your-api-key>
   ```
   ✅ **Confirmed:** the response is `Content-Type: text/plain` and the **entire body is a raw JWT** —
   there is no JSON wrapper and no `access_token` field. The JWT itself is the bearer token.
3. **Call data endpoints** with `Authorization: Bearer <jwt>`. ✅ Confirmed 200 on
   `/userprofile-service/userprofile/settings`.

**Confirmed auth facts:**
- **Token = raw JWT** returned as plain text from the token endpoint.
- **Data-call header:** `Authorization: Bearer <jwt>`.
- **Lifetime: 24 hours.** The JWT payload carries `iat`/`exp` exactly 86400s apart. There is **no
  refresh token** — re-mint from the API key when the JWT expires (or on a `401`).
- **Scopes** (from the JWT payload), all read-only: `CONNECT_READ`, `PERSONAL_API_FITNESS_READ`,
  `PERSONAL_API_NUTRITION_READ`, `PERSONAL_API_USER_READ`, `PERSONAL_API_WELLNESS_READ`. Issuer
  `https://diauth.garmin.com`.
- **Secret hygiene:** never log the API key or the JWT. (The spike printed a truncated JWT because
  the body is plain text; the real client must mask/omit it.)

**Still open:** rate limits (none documented; be conservative).

## Live-verification status (2026-10-24)

Implemented in `garmin_retriever.client` and confirmed returning data:

| Endpoint | Client method | Notes |
|---|---|---|
| `weight/range` | `weight_range(s, e, include_all=)` | ✅ (weight/all is broken — see below) |
| `fitnessage/v2/{date}` | `fitness_age(date)` | ✅ single date |
| `hrv/{date}` | `hrv(date)` | ✅ single date (204 → `None`) |
| `hrv/daily/{from}/{to}` | `hrv_daily(s, e)` | ✅ range; chunked at 28d |
| `sleep/dailySleep` | `daily_sleep(date)` | ✅ single date |
| `sleep/dailySleepSummariesByDate` | `sleep_summaries(s, e)` | ✅ range; chunked at 31d |
| `stats/steps/daily/{s}/{e}` | `steps_daily(s, e)` | ✅ range; chunked at 28d |
| `stats/stress/daily/{s}/{e}` | `stress_daily(s, e)` | ✅ range; chunked at 28d |
| `wellness/bodyBattery/reports/daily` | `body_battery_daily(s, e)` | ✅ range; chunked at 31d |
| `wellness/dailyHeartRate` | `daily_heart_rate(date)` | ✅ single date |

Remaining endpoints added 2026-10-25 (all live-verified):

| Endpoint | Client method | Notes |
|---|---|---|
| `usersummary/usersummary/daily` | `user_summary_daily(date)` | ✅ single date; flat, rich daily summary |
| `usersummary/v2/dailysummaries` | `daily_summaries_v2(s, e)` | ✅ range (chunked 1y); nested — library only, no CSV builder |
| `stats/hydration/daily/{s}/{e}` | `hydration_daily(s, e)` | ✅ range (31d); empty on this account |
| `wellness/daily/spo2acclimation/{date}` | `spo2_acclimation(date)` | ✅ single date |
| `nutrition/food/logs/{date}` | `nutrition_log(date)` | ✅ single date |
| `menstrualcycle/summary/{date}` | `menstrual_summary(date)` | ✅ single date (204 → None on this account) |
| `menstrualcycle/dayview/{date}` | `menstrual_dayview(date)` | ✅ single date; library only |
| `goal/.../weightgoal/{s}/{e}` | `weight_goal(s, e)` | ✅ range; empty on this account |
| `wellnessactivity/.../range/{from}/{until}` | `wellness_activities(s, e)` | ✅ range; empty on this account |
| `activities/search/activities` | `activities(s, e)` | ✅ range via startDate/endDate; auto-paginated |
| `userprofile/settings` | `user_profile_settings()` | ✅ no date (one-shot) |
| `biometric/heartRateZones/v2` | `heart_rate_zones()` | ✅ no date (one-shot) |
| `activity/{id}` | `activity(id)` | ✅ by id; nested → JSON output |
| `activity/{id}/workouts` | `activity_workouts(id)` | ✅ by id → JSON output |
| `download/files/activity/{id}` | `download_activity(id)` | ✅ by id; original file as **zip bytes** |

That is every endpoint in the spec except the broken `weight/all` — 25 of 26.

Range endpoints are auto-chunked to the caps above and concatenated (verified contiguous, no
duplicates, across a cap boundary). Values that are durations are in seconds; weights in grams.

## Conventions

- **Dates** are ISO `YYYY-MM-DD` strings (spec examples: `2026-08-31`). Used both as path segments
  and query params depending on the endpoint.
- **Responses** are `application/json`, except the activity file download, which returns
  `application/x-zip-compressed` (a zipped original activity file, e.g. FIT).
- **Date-range caps** vary per endpoint (noted below) — the retriever must chunk long ranges.
- **Error codes** seen in the spec: `400, 401, 403, 404, 500` (and `204 No Content` for HRV when no
  data exists for the date).

## Endpoints by service

### activity-service
| Method | Path | Notes |
|---|---|---|
| GET | `/activity-service/activity/{activityId}` | Summary, metadata, measurements, split summary for one activity. |
| GET | `/activity-service/activity/{activityId}/workouts` | Workouts performed during an activity. |

### activitylist-service
| Method | Path | Notes |
|---|---|---|
| GET | `/activitylist-service/activities/search/activities` | Paginated activity search. This is the primary way to **enumerate** activities. |

Key query params: `start` (int, default `0`), `limit` (int, default `99`), `sortBy`,
`sortOrder` (default `desc`), `startDate`/`endDate`, `activityType`, `activitySubType`, `eventType`,
`search`, plus many range filters (distance, duration, elevation, power, dive depth/bottom time,
geographic bounding box via `upperLatitude`/`rightLongitude`/`lowerLatitude`/`leftLongitude`),
`favorite`, `excludeChildren`. Pagination is offset-based (`start` + `limit`).

### download-service
| Method | Path | Notes |
|---|---|---|
| GET | `/download-service/files/activity/{activityId}` | Original activity file as a **zip** (`application/x-zip-compressed`). |

### biometric-service
| Method | Path | Notes |
|---|---|---|
| GET | `/biometric-service/heartRateZones/v2` | HR zone configuration. Query: `generateDefaults`. |

### fitnessage-service
| Method | Path | Notes |
|---|---|---|
| GET | `/fitnessage-service/fitnessage/v2/{calendarDate}` | Latest Fitness Age as of a date. Query: `fullHistoryScan`. |

### goal-service
| Method | Path | Notes |
|---|---|---|
| GET | `/goal-service/goal/user/effective/weightgoal/{startDate}/{endDate}` | Effective weight goals/ranges over an interval. |

### hrv-service
| Method | Path | Notes |
|---|---|---|
| GET | `/hrv-service/hrv/{calendarDate}` | HRV for one date (`204` if none). |
| GET | `/hrv-service/hrv/daily/{fromDate}/{toDate}` | HRV daily summaries over a range. |

### nutrition-service
| Method | Path | Notes |
|---|---|---|
| GET | `/nutrition-service/food/logs/{date}` | Daily nutrition summary. Query: `includeGoals`, `includeNutrition`, `includeMedia`, `mealId`. |

### periodichealth-service
| Method | Path | Notes |
|---|---|---|
| GET | `/periodichealth-service/menstrualcycle/summary/{calendarDate}` | Menstrual cycle summary. |
| GET | `/periodichealth-service/menstrualcycle/dayview/{calendarDate}` | Detailed day view. Query: `todayDate`, `reducedResponse`, `skipbm`, `includeAnalysis`. |

### sleep-service
| Method | Path | Notes |
|---|---|---|
| GET | `/sleep-service/sleep/dailySleep` | Daily sleep for one date. Query: `date`. |
| GET | `/sleep-service/sleep/dailySleepSummariesByDate` | Sleep summaries over a range. Query: `startDate`, `endDate`. **Max 31 days.** |

### userprofile-service
| Method | Path | Notes |
|---|---|---|
| GET | `/userprofile-service/userprofile/settings` | User profile settings. Good first "is-auth-working" call (no params). |

### usersummary-service
| Method | Path | Notes |
|---|---|---|
| GET | `/usersummary-service/stats/hydration/daily/{startDate}/{endDate}` | Daily hydration. **Max 31 days.** |
| GET | `/usersummary-service/stats/steps/daily/{startDate}/{endDate}` | Daily steps. **Max 28 days.** |
| GET | `/usersummary-service/stats/stress/daily/{startDate}/{endDate}` | Daily stress. **Max 28 days.** |
| GET | `/usersummary-service/usersummary/daily` | Full daily summary (steps, calories, stress, Body Battery…). Query: `calendarDate`. |
| GET | `/usersummary-service/v2/dailysummaries` | Daily summaries over a range. Query: `startDate`, `endDate`. **Max 1 year.** |

### weight-service
| Method | Path | Notes |
|---|---|---|
| GET | `/weight-service/weight/all/{startDate}/{endDate}` | ⚠️ **Broken on the live gateway** — returns `400 {}` for every input (verified 2026-10-24). Use `weight/range` instead. |
| GET | `/weight-service/weight/range/{startDate}/{endDate}` | ✅ Working. Weight summaries (daily latest, min/max, average, adjacent). Query `includeAll=true` adds every entry per day in `allWeightMetrics` — the functional equivalent of `weight/all`. **Weights are in grams.** |

### wellness-service
| Method | Path | Notes |
|---|---|---|
| GET | `/wellness-service/wellness/bodyBattery/reports/daily` | Body Battery daily reports. Query: `startDate`, `endDate`, `chunks`. **Max 31 days.** |
| GET | `/wellness-service/wellness/daily/spo2acclimation/{calendarDate}` | Daily SpO2 readings. |
| GET | `/wellness-service/wellness/dailyHeartRate` | Daily heart rate. Query: `date`. |

### wellnessactivity-service
| Method | Path | Notes |
|---|---|---|
| GET | `/wellnessactivity-service/activity/summary/range/{fromDate}/{untilDate}` | Wellness activity summaries over an inclusive date range. |

## Range-cap summary (for chunking)

| Endpoint | Max span |
|---|---|
| `usersummary/v2/dailysummaries` | 1 year |
| sleep `dailySleepSummariesByDate`, hydration, bodyBattery reports | 31 days |
| steps, stress | 28 days |
| others | per-date or unspecified |

The response schemas (109 of them) are all in the OpenAPI file under `components.schemas`; consult it
for exact field shapes when modeling data.
