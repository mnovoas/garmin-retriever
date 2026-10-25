# Endpoints

The Garmin Connect **Personal API** (base `https://personal.connectapi.garmin.com`). All endpoints are read-only `GET`s and return only the authenticated user's own data. Source of truth: `openapi/garmin-personal-api.openapi.json`.

Each entry lists parameters, the CLI command / client method that wraps it, and the top-level response fields (nested DTO field names reference schemas in the OpenAPI file). `(library)` = available as a client method but not a dedicated CLI command.


## activity-service

### `GET /activity-service/activity/{activityId}`

Retrieves the activity summary, metadata, measurements, and split summary information for the specified activity.

- **CLI:** `activity --id N` · **Client:** `activity(id)`
- **Parameters:**
  - `activityId` (path, integer) *(required)* — The ID of the activity to retrieve the summary
- **Response** (object):
  - `activityId`: integer
  - `activityUUID`: UUID
  - `activityName`: string
  - `description`: string
  - `userProfileId`: integer
  - `parentId`: integer
  - `parentName`: string
  - `isMultiSportParent`: boolean
  - `activityTypeDTO`: ActivityTypeDTO
  - `eventTypeDTO`: EventTypeDTO
  - `accessControlRuleDTO`: AccessControlRuleDTO
  - `timeZoneUnitDTO`: TimeZoneUnitDTO
  - `metadataDTO`: MetadataDTO
  - `summaryDTO`: SummaryDTO
  - `locationName`: string
  - `diveInfo`: DiveInfoDTO
  - `splitSummaries`: array<SplitSummaryDTO>
  - `videoGameInfo`: VideoGameInfoDTO
  - `deviceDisplayUnitsDTO`: DeviceDisplayUnitsDTO

### `GET /activity-service/activity/{activityId}/workouts`

Retrieves workouts performed during an activity

- **CLI:** `workouts --id N` · **Client:** `activity_workouts(id)`
- **Parameters:**
  - `activityId` (path, integer) *(required)* — The ID of the activity for which to retrieve workouts
- **Response** (list of objects):
  - `index`: integer
  - `workoutName`: string
  - `timeCreated`: string
  - `sport`: string
  - `manufacturer`: string
  - `multisportSet`: integer
  - `steps`: array<WorkoutStepDTO>
  - `workoutPhrase`: string


## activitylist-service

### `GET /activitylist-service/activities/search/activities`

Searches activities using the supplied filters and returns matching paginated activity summaries.

- **CLI:** `activities` · **Client:** `activities(s,e)`
- **Note:** auto-paginated via startDate/endDate
- **Parameters:**
  - `start` (query, integer, default `0`) — Zero-based offset of the first activity to return. Defaults to 0.
  - `limit` (query, integer, default `99`) — Maximum number of activities to return. Defaults to 99.
  - `favorite` (query, integer, default `-1`) — Filter by favorite status: 1 returns favorites, 0 returns non-favorites, and -1 applies no favorite filter. Defaults to -1.
  - `sortOrder` (query, string, default `desc`) — Sort direction: asc for ascending or desc for descending, case-insensitive. Defaults to desc.
  - `excludeChildren` (query, boolean, default `True`) — Whether to exclude child activities that have a parent activity, such as individual legs of a multisport activity. Defaults to true.
  - `sortBy` (query, string) — Activity field to sort by, such as name, distance, or duration. Defaults to startLocal, the activity's local start date and time.
  - `search` (query, string) — Text to search for in activity names and descriptions.
  - `activityType` (query, string) — Parent activity type key to include, such as running or cycling. Must identify a parent type, not a subtype.
  - `activitySubType` (query, string) — Activity subtype key to include. Must identify a child type and, if activityType is also provided, belong to that parent type. For example, use activitySubType=trail_running with activityType=running, or activitySubType=road_cycling with activityType=cycling.
  - `eventType` (query, string) — Event classification key to include, such as race, training, recreation, fitness, specialEvent, or uncategorized.
  - `minDistance` (query, integer) — Inclusive minimum activity distance, in meters.
  - `maxDistance` (query, integer) — Inclusive maximum activity distance, in meters.
  - `minDuration` (query, integer) — Inclusive minimum activity timer duration, in seconds.
  - `maxDuration` (query, integer) — Inclusive maximum activity timer duration, in seconds.
  - `minElevation` (query, integer) — Inclusive minimum total elevation gain for the activity, in meters.
  - `maxElevation` (query, integer) — Inclusive maximum total elevation gain for the activity, in meters.
  - `startDate` (query, string) — Inclusive earliest activity start date, based on the activity's local start time, in YYYY-MM-DD format.
  - `endDate` (query, string) — Inclusive latest activity start date, based on the activity's local start time, in YYYY-MM-DD format.
  - `upperLatitude` (query, number) — Northern latitude boundary of the bounding box for activity start locations, in decimal degrees. Provide all four latitude and longitude boundaries to apply this filter.
  - `rightLongitude` (query, number) — Eastern longitude boundary of the bounding box for activity start locations, in decimal degrees. Provide all four latitude and longitude boundaries to apply this filter.
  - `lowerLatitude` (query, number) — Southern latitude boundary of the bounding box for activity start locations, in decimal degrees. Provide all four latitude and longitude boundaries to apply this filter.
  - `leftLongitude` (query, number) — Western longitude boundary of the bounding box for activity start locations, in decimal degrees. Provide all four latitude and longitude boundaries to apply this filter.
  - `lowerMaxDepth` (query, integer) — Inclusive lower bound on the dive activity's maximum depth, in centimeters.
  - `upperMaxDepth` (query, integer) — Inclusive upper bound on the dive activity's maximum depth, in centimeters.
  - `decoDive` (query, boolean) — Filter by decompression dive status: true returns decompression dives and false returns activities marked as non-decompression dives. Omit to apply no decompression dive filter.
  - `minElapsedDuration` (query, integer) — Inclusive minimum total elapsed activity duration, including paused time, in seconds.
  - `maxElapsedDuration` (query, integer) — Inclusive maximum total elapsed activity duration, including paused time, in seconds.
  - `minBottomTime` (query, integer) — Inclusive minimum dive bottom time, in seconds.
  - `maxBottomTime` (query, integer) — Inclusive maximum dive bottom time, in seconds.
  - `minAvgPower` (query, integer) — Inclusive minimum average activity power, in watts.
  - `excludedActivitySubType` (query, array) — Activity subtype keys to exclude. Repeat this query parameter to exclude multiple subtypes.
  - `requiredField` (query, array) — Activity fields that must have a non-null value for an activity to be included. Repeat this query parameter to require multiple fields; all specified fields must be present.
- **Response** (list of objects):
  - `activityId`: integer
  - `activityName`: string
  - `description`: string
  - `startTimeLocal`: string
  - `startTimeGMT`: string
  - `activityType`: ActivityTypeDTO
  - `eventType`: EventTypeDTO
  - `comments`: array<ActivityCommentDTO>
  - `isFavorite`: boolean
  - `isPR`: boolean
  - `isAutoCalcCalories`: boolean
  - `isParent`: boolean
  - `parentId`: integer
  - `distance`: number
  - `duration`: number
  - `elapsedDuration`: number
  - `movingDuration`: number
  - `elevationGain`: number
  - `elevationLoss`: number
  - `averageSpeed`: number
  - `maxSpeed`: number
  - `startLatitude`: number
  - `startLongitude`: number
  - `hasPolyline`: boolean
  - `hasImages`: boolean
  - `ownerId`: integer
  - `ownerDisplayName`: string
  - `ownerFullName`: string
  - `ownerProfileImageUrlSmall`: string
  - `ownerProfileImageUrlMedium`: string
  - `ownerProfileImageUrlLarge`: string
  - `calories`: number
  - `bmrCalories`: number
  - `averageHR`: number
  - `maxHR`: number
  - `averageRunningCadenceInStepsPerMinute`: number
  - `maxRunningCadenceInStepsPerMinute`: number
  - `maxLapAvgRunCadence`: number
  - `averageBikingCadenceInRevPerMinute`: number
  - `maxBikingCadenceInRevPerMinute`: number
  - `averageSwimCadenceInStrokesPerMinute`: number
  - `maxSwimCadenceInStrokesPerMinute`: number
  - `averageSwolf`: number
  - `activeLengths`: integer
  - `steps`: integer
  - `numberOfActivityLikes`: integer
  - `numberOfActivityComments`: integer
  - `likedByUser`: boolean
  - `commentedByUser`: boolean
  - `activityLikeDisplayNames`: array<string>
  - `activityLikeFullNames`: array<string>
  - `activityLikeProfileImageUrls`: array<string>
  - `requestorRelationship`: string
  - `privacy`: AccessControlRuleDTO
  - `poolLength`: number
  - `unitOfPoolLength`: UnitDTO
  - `hasVideo`: boolean
  - `videoUrl`: string
  - `beginTimestamp`: integer
  - `sportTypeId`: integer
  - `avgPower`: number
  - `maxPower`: number
  - `aerobicTrainingEffect`: number
  - `anaerobicTrainingEffect`: number
  - `strokes`: number
  - `normPower`: number
  - `leftBalance`: number
  - `rightBalance`: number
  - `avgLeftBalance`: number
  - `max20MinPower`: number
  - `avgVerticalOscillation`: number
  - `avgGroundContactTime`: number
  - `avgStrideLength`: number
  - `avgFractionalCadence`: number
  - `maxFractionalCadence`: number
  - `trainingStressScore`: number
  - `intensityFactor`: number
  - `vO2MaxValue`: number
  - `avgVerticalRatio`: number
  - `avgGroundContactBalance`: number
  - `lactateThresholdBpm`: number
  - `getlactateThresholdSpeed`: number
  - `maxFtp`: number
  - `avgStrokeDistance`: number
  - `avgStrokeCadence`: number
  - `maxStrokeCadence`: number
  - `avgStrokes`: number
  - `minStrokes`: number
  - `minTemperature`: number
  - `maxTemperature`: number
  - `minElevation`: number
  - `maxElevation`: number
  - `avgElevation`: number
  - `avgDoubleCadence`: number
  - `maxDoubleCadence`: number
  - `isElevationCorrected`: boolean
  - `summarizedExerciseSets`: array<SummarizedExerciseSet>
  - `maxDepth`: number
  - `avgDepth`: number
  - `surfaceInterval`: number
  - `startN2`: number
  - `endN2`: number
  - `startCns`: number
  - `endCns`: number
  - `isDecoDive`: boolean
  - `summarizedDiveInfo`: SummarizedDiveInfoDTO
  - `diveCount`: integer
  - `activityLikeAuthors`: array<UserInfoDto>
  - `avgVerticalSpeed`: number
  - `maxVerticalSpeed`: number
  - `floorsClimbed`: number
  - `floorsDescended`: number
  - `manufacturer`: string
  - `diveNumber`: integer
  - `locationName`: string
  - `bottomTime`: number
  - `lapCount`: integer
  - `endLatitude`: number
  - `endLongitude`: number
  - `flow`: number
  - `grit`: number
  - `jumpCount`: integer
  - `caloriesEstimated`: number
  - `caloriesConsumed`: number
  - `waterEstimated`: number
  - `waterConsumed`: number
  - `maxAvgPower_1`: integer
  - `maxAvgPower_2`: integer
  - `maxAvgPower_5`: integer
  - `maxAvgPower_10`: integer
  - `maxAvgPower_20`: integer
  - `maxAvgPower_30`: integer
  - `maxAvgPower_60`: integer
  - `maxAvgPower_120`: integer
  - `maxAvgPower_300`: integer
  - `maxAvgPower_600`: integer
  - `maxAvgPower_1200`: integer
  - `maxAvgPower_1800`: integer
  - `maxAvgPower_3600`: integer
  - `maxAvgPower_7200`: integer
  - `maxAvgPower_18000`: integer
  - `excludeFromPowerCurveReports`: boolean
  - `totalSets`: integer
  - `activeSets`: integer
  - `totalReps`: integer
  - `minRespirationRate`: number
  - `maxRespirationRate`: number
  - `avgRespirationRate`: number
  - `trainingEffectLabel`: string
  - `activityTrainingLoad`: number
  - `avgFlow`: number
  - `avgGrit`: number
  - `minActivityLapDuration`: number
  - `avgStress`: number
  - `startStress`: number
  - `endStress`: number
  - `differenceStress`: number
  - `maxStress`: number
  - `aerobicTrainingEffectMessage`: string
  - `anaerobicTrainingEffectMessage`: string
  - `splitSummaries`: array<MinimalSplitSummaryDTO>
  - `isManualActivity`: boolean
  - `moderateIntensityMinutes`: integer
  - `vigorousIntensityMinutes`: integer
  - `maxBottomTime`: number
  - `hasSeedFirstbeatProfile`: boolean
  - `avgGradeAdjustedSpeed`: number
  - `avgWheelchairCadence`: number
  - `maxWheelchairCadence`: number
  - `avgJumpRopeCadence`: number
  - `maxJumpRopeCadence`: number
  - `gameName`: string
  - `differenceBodyBattery`: integer
  - `gameType`: string
  - `beginPackWeight`: number
  - `fastestSplit_1000`: number
  - `fastestSplit_1609`: number
  - `fastestSplit_5000`: number
  - `fastestSplit_10000`: number
  - `fastestSplit_21098`: number
  - `fastestSplit_42195`: number
  - `fastestSplit_40000`: number
  - `fastestSplit_100`: number
  - `fastestSplit_400`: number
  - `fastestSplit_750`: number
  - `fastestSplit_1500`: number
  - `fastestSplit_91`: number
  - `fastestSplit_457`: number
  - `fastestSplit_914`: number
  - `fastestSplit_1508`: number
  - `impactLoad`: number
  - `avgStepSpeedLoss`: number
  - `avgStepSpeedLossPercent`: number
  - `hrTimeInZone_1`: number
  - `hrTimeInZone_2`: number
  - `hrTimeInZone_3`: number
  - `hrTimeInZone_4`: number
  - `hrTimeInZone_5`: number
  - `powerTimeInZone_1`: number
  - `powerTimeInZone_2`: number
  - `powerTimeInZone_3`: number
  - `powerTimeInZone_4`: number
  - `powerTimeInZone_5`: number
  - `powerTimeInZone_6`: number
  - `powerTimeInZone_7`: number
  - `longestPoolApneaInterval`: number
  - `avgForce`: number
  - `maxForce`: number
  - `normalizedForce`: number
  - `poolApneaBreathHoldDuration`: number
  - `deviceDisplayUnitsDTO`: DeviceDisplayUnitsDTO
  - `endTimeGMT`: string
  - `qualifyingDive`: boolean
  - `multiDayActivityUUIDs`: array<string>
  - `activityUUID`: string
  - `carbonOffset`: number
  - `packWeightCalories`: integer
  - `standingTime`: number
  - `seatedTime`: number
  - `maxStandingPower`: number
  - `maxSeatedPower`: number
  - `avgStandingPower`: number
  - `avgSeatedPower`: number
  - `parent`: boolean
  - `decoDive`: boolean
  - `elevationCorrected`: boolean
  - `pr`: boolean
  - `manualActivity`: boolean
  - `favorite`: boolean
  - `autoCalcCalories`: boolean


## biometric-service

### `GET /biometric-service/heartRateZones/v2`

Retrieve the user's heart rate zone configuration.

- **CLI:** `hrzones` · **Client:** `heart_rate_zones()`
- **Parameters:**
  - `generateDefaults` (query, boolean, default `True`) — Whether to generate default zones when the user has no configured zones.
- **Response** (list of objects):
  - `trainingMethod`: string
  - `restingHeartRateUsed`: integer
  - `lactateThresholdHeartRateUsed`: integer
  - `zone1Floor`: integer
  - `zone2Floor`: integer
  - `zone3Floor`: integer
  - `zone4Floor`: integer
  - `zone5Floor`: integer
  - `maxHeartRateUsed`: integer
  - `restingHrAutoUpdateUsed`: boolean
  - `sport`: string


## download-service

### `GET /download-service/files/activity/{activityId}`

Download an activity file in its original format.

- **CLI:** `download --id N` · **Client:** `download_activity(id)`
- **Note:** returns a zip (original file)
- **Parameters:**
  - `activityId` (path, integer) *(required)*
- **Response:** `application/x-zip-compressed`


## fitnessage-service

### `GET /fitnessage-service/fitnessage/v2/{calendarDate}`

Returns the lastest Fitness Age information as of the target calendar date.

- **CLI:** `fitnessage` · **Client:** `fitness_age(date)`
- **Parameters:**
  - `calendarDate` (path, string) *(required)* — The target date; Fitness Age information returned will be the latest available as of this date.
  - `fullHistoryScan` (query, boolean, default `True`) — Whether to scan the full history to find the latest Fitness Age information. If false, only the last 28 days relative to the target calendar date will be considered.
- **Response** (list of objects):
  - `chronologicalAge`: integer
  - `fitnessAge`: number
  - `achievableFitnessAge`: number
  - `previousFitnessAge`: number
  - `components`: object
  - `lastUpdated`: string
  - `invalidReason`: string


## goal-service

### `GET /goal-service/goal/user/effective/weightgoal/{startDate}/{endDate}`

Returns the authenticated user's effective weight goals and weight goal ranges for the requested date interval.

- **CLI:** `weightgoal` · **Client:** `weight_goal(s,e)`
- **Parameters:**
  - `startDate` (path, string) *(required)* — Beginning of the requested date interval.
  - `endDate` (path, string) *(required)* — End of the requested date interval.
- **Response** (object):
  - `userGoals`: array<UserGoalDTO>
  - `userGoalRanges`: array<UserGoalHighLowRangeDTO>


## hrv-service

### `GET /hrv-service/hrv/{calendarDate}`

Get HRV data for a specific date

- **CLI:** `(library)` · **Client:** `hrv(date)`
- **Note:** detailed daily HRV incl. hrvReadings
- **Parameters:**
  - `calendarDate` (path, string) *(required)*
- **Response** (object):
  - `userProfilePk`: integer
  - `hrvSummary`: HrvSummaryDTO
  - `hrvReadings`: array<HrvReadingDTO>
  - `startTimestampGMT`: string
  - `endTimestampGMT`: string
  - `startTimestampLocal`: string
  - `endTimestampLocal`: string
  - `sleepStartTimestampGMT`: string
  - `sleepEndTimestampGMT`: string
  - `sleepStartTimestampLocal`: string
  - `sleepEndTimestampLocal`: string

### `GET /hrv-service/hrv/daily/{fromDate}/{toDate}`

Get HRV daily summaries for a date range

- **CLI:** `hrv` · **Client:** `hrv_daily(s,e)`
- **Parameters:**
  - `fromDate` (path, string) *(required)*
  - `toDate` (path, string) *(required)*
- **Response** (object):
  - `hrvSummaries`: array<HrvSummaryDTO>
  - `userProfilePk`: integer


## nutrition-service

### `GET /nutrition-service/food/logs/{date}`

Retrieves the user's daily nutrition summary for a specific calendar date. This includes the user's nutrition goals, nutrients consumed, and discrete events for the day. The response can optionally include meal-by-meal breakdowns of calories and other nutrients consumed by the user on the given date.

- **CLI:** `nutrition` · **Client:** `nutrition_log(date)`
- **Parameters:**
  - `includeGoals` (query, boolean, default `True`) — Goals are included by default unless requested with includeGoals=false
  - `includeNutrition` (query, boolean, default `True`) — Nutrition information is included by default unless requested with includeNutrition=false
  - `includeMedia` (query, boolean, default `True`) — Images is included by default unless requested with includeMedia=false
  - `mealId` (query, integer) — Id of the meal like id for Breakfast, Lunch, Snacks or Dinner
  - `date` (path, string) *(required)* — Date for which to retrieve the daily nutrition logs. Date must be in the YYYY-MM-DD format. The date is interpreted in the user's local timezone.
- **Response** (object):
  - `dailyNutritionContent`: ThinNutritionContentDTO
  - `dailyNutritionGoals`: NutritionGoalsDTO
  - `dayEndTime`: LocalTime
  - `dayStartTime`: LocalTime
  - `loggedFoodsWithServingSizes`: array<FoodDTO>
  - `mealDate`: string
  - `mealDetails`: array<MealDetailsDTO>


## periodichealth-service

### `GET /periodichealth-service/menstrualcycle/summary/{calendarDate}`

Returns a summary of the user's menstrual cycle.

- **CLI:** `menstrual` · **Client:** `menstrual_summary(date)`
- **Parameters:**
  - `calendarDate` (path, string) *(required)* — The calendar date (yyyy-MM-dd) to retrieve data for.
- **Response** (object):
  - `analysis`: MenstrualCycleAnalysisDTO
  - `currentPhase`: integer
  - `cycleType`: string
  - `dayInCycle`: integer
  - `daysUntilNextPhase`: integer
  - `deliveryDate`: ConnectDate
  - `dueDate`: ConnectDate
  - `educationContentMod`: integer
  - `endDate`: ConnectDate
  - `feedbackPhrase`: string
  - `fertileWindowStart`: integer
  - `isSkinTempMct`: boolean
  - `lengthOfCurrentPhase`: integer
  - `lengthOfFertileWindow`: integer
  - `lutealPhaseStart`: integer
  - `numberOfWeek`: integer
  - `overlapCycleList`: array<OverlapCycle>
  - `periodLength`: integer
  - `predictedCycle`: boolean
  - `predictedCycleLength`: integer
  - `predictedOvulationDate`: ConnectDate
  - `pregnancyCycle`: boolean
  - `startDate`: ConnectDate

### `GET /periodichealth-service/menstrualcycle/dayview/{calendarDate}`

Returns detailed menstrual cycle information for a single calendar day, combining the user's logged daily data (symptoms, flow, mood, etc.), the cycle summary for that day, and (for pregnancy tracking) weekly weight goal ranges.

- **CLI:** `(library)` · **Client:** `menstrual_dayview(date)`
- **Parameters:**
  - `calendarDate` (path, string) *(required)* — The calendar date (yyyy-MM-dd) to retrieve data for.
  - `todayDate` (query, string) — The current calendar date (yyyy-MM-dd) from the caller's perspective, used as a reference point for predictions and calculations.
  - `reducedResponse` (query, boolean, default `False`) — When true, returns a reduced/lightweight version of the response payload.
  - `skipbm` (query, boolean, default `False`) — When true, excludes baby movement (kick count) data from the response.
  - `includeAnalysis` (query, boolean, default `False`) — When true, includes menstrual cycle analysis data in the response.
- **Response** (object):
  - `dayLog`: DailyMenstrualCycleLogDTO
  - `daySummary`: MenstrualCycleSummaryDTO
  - `weightGoals`: WeightGoalRangeDTO


## sleep-service

### `GET /sleep-service/sleep/dailySleep`

Retrieves daily sleep data for a calendar date

- **CLI:** `(library)` · **Client:** `daily_sleep(date)`
- **Note:** detailed single-day sleep
- **Parameters:**
  - `date` (query, string)
- **Response** (object):
  - `id`: integer
  - `userProfilePK`: integer
  - `calendarDate`: string
  - `sleepTimeSeconds`: integer
  - `napTimeSeconds`: integer
  - `sleepWindowConfirmed`: boolean
  - `sleepWindowConfirmationType`: string
  - `sleepStartTimestampGMT`: string
  - `sleepEndTimestampGMT`: string
  - `sleepStartTimestampLocal`: string
  - `sleepEndTimestampLocal`: string
  - `autoSleepStartTimestampGMT`: string
  - `autoSleepEndTimestampGMT`: string
  - `sleepQualityTypePK`: string
  - `sleepResultTypePK`: string
  - `unmeasurableSleepSeconds`: integer
  - `deepSleepSeconds`: integer
  - `lightSleepSeconds`: integer
  - `remSleepSeconds`: integer
  - `awakeSleepSeconds`: integer
  - `deviceRemCapable`: boolean
  - `sleepFromDevice`: boolean
  - `averageSpO2Value`: number
  - `lowestSpO2Value`: integer
  - `highestSpO2Value`: integer
  - `numberOfEventsBelowThreshold`: integer
  - `averageSpO2HRSleep`: number
  - `spo2Threshold`: integer
  - `averageRespirationValue`: number
  - `lowestRespirationValue`: number
  - `highestRespirationValue`: number
  - `awakeCount`: integer
  - `avgSleepStress`: number
  - `ageGroup`: string
  - `avgHeartRate`: number
  - `sleepScoreFeedback`: string
  - `sleepScoreInsight`: string
  - `sleepScorePersonalizedInsight`: string
  - `sleepScores`: object
  - `userNote`: string
  - `kidSleepNote`: string
  - `sleepVersion`: integer
  - `sleepNeed`: SleepNeedDTO
  - `nextSleepNeed`: SleepNeedDTO
  - `dailyNapDTOS`: array<DailyNapDTO>
  - `breathingDisruptionSeverity`: string
  - `sleepAlignment`: SleepAlignmentDto

### `GET /sleep-service/sleep/dailySleepSummariesByDate`

Retrieves daily sleep summaries data for a date range, up to a maximum of 31 days.

- **CLI:** `sleep` · **Client:** `sleep_summaries(s,e)`
- **Note:** max 31 days per call (auto-chunked)
- **Parameters:**
  - `startDate` (query, string)
  - `endDate` (query, string)
- **Response** (list of objects):
  - `id`: integer
  - `userProfilePK`: integer
  - `calendarDate`: string
  - `sleepTimeSeconds`: integer
  - `napTimeSeconds`: integer
  - `sleepWindowConfirmed`: boolean
  - `sleepWindowConfirmationType`: string
  - `sleepStartTimestampGMT`: string
  - `sleepEndTimestampGMT`: string
  - `sleepStartTimestampLocal`: string
  - `sleepEndTimestampLocal`: string
  - `autoSleepStartTimestampGMT`: string
  - `autoSleepEndTimestampGMT`: string
  - `sleepQualityTypePK`: string
  - `sleepResultTypePK`: string
  - `unmeasurableSleepSeconds`: integer
  - `deepSleepSeconds`: integer
  - `lightSleepSeconds`: integer
  - `remSleepSeconds`: integer
  - `awakeSleepSeconds`: integer
  - `deviceRemCapable`: boolean
  - `sleepFromDevice`: boolean
  - `averageSpO2Value`: number
  - `lowestSpO2Value`: integer
  - `highestSpO2Value`: integer
  - `numberOfEventsBelowThreshold`: integer
  - `averageSpO2HRSleep`: number
  - `spo2Threshold`: integer
  - `averageRespirationValue`: number
  - `lowestRespirationValue`: number
  - `highestRespirationValue`: number
  - `awakeCount`: integer
  - `avgSleepStress`: number
  - `ageGroup`: string
  - `avgHeartRate`: number
  - `sleepScoreFeedback`: string
  - `sleepScoreInsight`: string
  - `sleepScorePersonalizedInsight`: string
  - `sleepScores`: object
  - `userNote`: string
  - `kidSleepNote`: string
  - `sleepVersion`: integer
  - `sleepNeed`: SleepNeedDTO
  - `nextSleepNeed`: SleepNeedDTO
  - `dailyNapDTOS`: array<DailyNapDTO>
  - `breathingDisruptionSeverity`: string
  - `sleepAlignment`: SleepAlignmentDto


## userprofile-service

### `GET /userprofile-service/userprofile/settings`

Retrieve the user profile settings.

- **CLI:** `profile` · **Client:** `user_profile_settings()`
- **Response** (object):
  - `displayName`: string
  - `preferredLocale`: string
  - `measurementSystem`: string
  - `firstDayOfWeek`: DayOfWeekDTO
  - `numberFormat`: string
  - `timeFormat`: UnitFormatDTO
  - `dateFormat`: UnitFormatDTO
  - `powerFormat`: UnitFormatDTO
  - `heartRateFormat`: UnitFormatDTO
  - `timeZone`: string
  - `hydrationMeasurementUnit`: string
  - `hydrationContainers`: array<HydrationContainer>
  - `glucoseMeasurementUnit`: string
  - `golfDistanceUnit`: string
  - `golfElevationUnit`: string
  - `golfSpeedUnit`: string
  - `wheelchairModeEnabled`: boolean
  - `availableTrainingDays`: array<string>
  - `preferredLongTrainingDays`: array<string>


## usersummary-service

### `GET /usersummary-service/stats/hydration/daily/{startDate}/{endDate}`

Get daily hydration data for a date range, up to a maximum of 31 days.

- **CLI:** `hydration` · **Client:** `hydration_daily(s,e)`
- **Note:** max 31 days (auto-chunked)
- **Parameters:**
  - `startDate` (path, string) *(required)*
  - `endDate` (path, string) *(required)*
- **Response** (list of objects):
  - `userId`: integer
  - `calendarDate`: string
  - `valueInML`: number
  - `goalInML`: number
  - `lastEntryTimestampLocal`: string
  - `sweatLossInML`: number
  - `activityIntakeInML`: number

### `GET /usersummary-service/stats/steps/daily/{startDate}/{endDate}`

Get daily steps data for a date range, up to a maximum of 28 days.

- **CLI:** `steps` · **Client:** `steps_daily(s,e)`
- **Note:** max 28 days (auto-chunked)
- **Parameters:**
  - `startDate` (path, string) *(required)*
  - `endDate` (path, string) *(required)*
- **Response** (list of objects):
  - `calendarDate`: string
  - `totalSteps`: integer
  - `totalDistance`: integer
  - `stepGoal`: integer

### `GET /usersummary-service/stats/stress/daily/{startDate}/{endDate}`

Get daily stress data for a date range, up to a maximum of 28 days.

- **CLI:** `stress` · **Client:** `stress_daily(s,e)`
- **Note:** max 28 days (auto-chunked)
- **Parameters:**
  - `startDate` (path, string) *(required)*
  - `endDate` (path, string) *(required)*
- **Response** (list of objects):
  - `calendarDate`: string
  - `values`: object

### `GET /usersummary-service/usersummary/daily`

Get user summary data for a specific date. User summary data includes steps, calories, stress, Body Battery, and other wellness metrics for the given date.

- **CLI:** `usersummary` · **Client:** `user_summary_daily(date)`
- **Parameters:**
  - `calendarDate` (query, string)
- **Response** (object):
  - `userProfileId`: integer
  - `displayName`: string
  - `totalKilocalories`: number
  - `activeKilocalories`: number
  - `bmrKilocalories`: number
  - `consumedKilocalories`: number
  - `remainingKilocalories`: number
  - `totalSteps`: integer
  - `netCalorieGoal`: integer
  - `totalDistanceMeters`: integer
  - `wellnessDistanceMeters`: integer
  - `userDailySummaryId`: integer
  - `calendarDate`: string
  - `uuid`: string
  - `dailyStepGoal`: integer
  - `dailyPushesGoal`: integer
  - `totalPushDistance`: integer
  - `totalPushes`: integer
  - `wellnessStartTimeGmt`: string
  - `wellnessStartTimeLocal`: string
  - `wellnessEndTimeGmt`: string
  - `wellnessEndTimeLocal`: string
  - `durationInMilliseconds`: integer
  - `wellnessDescription`: string
  - `highlyActiveSeconds`: integer
  - `activeSeconds`: integer
  - `sedentarySeconds`: integer
  - `sleepingSeconds`: integer
  - `includesWellnessData`: boolean
  - `includesActivityData`: boolean
  - `includesCalorieConsumedData`: boolean
  - `moderateIntensityMinutes`: integer
  - `vigorousIntensityMinutes`: integer
  - `floorsAscendedInMeters`: number
  - `floorsDescendedInMeters`: number
  - `floorsAscended`: number
  - `floorsDescended`: number
  - `intensityMinutesGoal`: integer
  - `userFloorsAscendedGoal`: integer
  - `minHeartRate`: integer
  - `maxHeartRate`: integer
  - `restingHeartRate`: integer
  - `lastSevenDaysAvgRestingHeartRate`: integer
  - `source`: string
  - `averageStressLevel`: integer
  - `maxStressLevel`: integer
  - `stressDuration`: integer
  - `restStressDuration`: integer
  - `activityStressDuration`: integer
  - `uncategorizedStressDuration`: integer
  - `totalStressDuration`: integer
  - `lowStressDuration`: integer
  - `mediumStressDuration`: integer
  - `highStressDuration`: integer
  - `stressPercentage`: number
  - `restStressPercentage`: number
  - `activityStressPercentage`: number
  - `uncategorizedStressPercentage`: number
  - `lowStressPercentage`: number
  - `mediumStressPercentage`: number
  - `highStressPercentage`: number
  - `stressQualifier`: string
  - `measurableAwakeDuration`: integer
  - `measurableAsleepDuration`: integer
  - `lastSyncTimestampGMT`: string
  - `minAvgHeartRate`: integer
  - `maxAvgHeartRate`: integer
  - `bodyBatteryChargedValue`: integer
  - `bodyBatteryDrainedValue`: integer
  - `bodyBatteryHighestValue`: integer
  - `bodyBatteryLowestValue`: integer
  - `bodyBatteryMostRecentValue`: integer
  - `bodyBatteryDuringSleep`: integer
  - `bodyBatteryAtWakeTime`: integer
  - `bodyBatteryVersion`: number
  - `abnormalHeartRateAlertsCount`: integer
  - `averageSpo2`: number
  - `lowestSpo2`: integer
  - `latestSpo2`: integer
  - `latestSpo2ReadingTimeGmt`: string
  - `latestSpo2ReadingTimeLocal`: string
  - `averageMonitoringEnvironmentAltitude`: number
  - `bodyBatteryDynamicFeedbackEvent`: BodyBatteryDynamicFeedbackEventDTO
  - `endOfDayBodyBatteryDynamicFeedbackEvent`: BodyBatteryDynamicFeedbackEventDTO
  - `bodyBatteryActivityEventList`: array<BodyBatteryActivityEventDTO>
  - `isJetLagDay`: boolean
  - `jetLagTripName`: string
  - `hydrationValueInML`: number
  - `hydrationGoalInML`: number
  - `avgWakingRespirationValue`: number
  - `highestRespirationValue`: number
  - `lowestRespirationValue`: number
  - `latestRespirationValue`: number
  - `latestRespirationTimeGMT`: string
  - `respirationAlgorithmVersion`: integer

### `GET /usersummary-service/v2/dailysummaries`

Get user daily summaries for a date range, up to a maximum of 1 year.

- **CLI:** `(library)` · **Client:** `daily_summaries_v2(s,e)`
- **Note:** nested per-day summaries; max 1 year
- **Parameters:**
  - `startDate` (query, string)
  - `endDate` (query, string)
- **Response** (object):
  - `data`: array<UserDailySummaryV2DTO>


## weight-service

### `GET /weight-service/weight/all/{startDate}/{endDate}`

Retrieve all weight entries for a specified date range.

- **CLI:** `—` · **Client:** `—`
- **Note:** BROKEN on live gateway (HTTP 400) — use weight/range
- **Parameters:**
  - `startDate` (path, string) *(required)* — The start date(user's local calendar) of the range, inclusive. Format yyyy-MM-dd.
  - `endDate` (path, string) *(required)* — The end date(user's local calendar) of the range, inclusive. Format yyyy-MM-dd.
- **Response** (list of objects):
  - `date`: string
  - `calendarDate`: string
  - `weight`: number
  - `bmi`: number
  - `bodyFat`: number
  - `bodyWater`: number
  - `boneMass`: integer
  - `muscleMass`: integer
  - `physiqueRating`: integer
  - `visceralFat`: integer
  - `metabolicAge`: number
  - `timestampGMT`: string
  - `weightDelta`: number

### `GET /weight-service/weight/range/{startDate}/{endDate}`

Retrieve weight summaries for a date range, including daily latest weights, the range average, and adjacent weights.

- **CLI:** `weight` · **Client:** `weight_range(s,e)`
- **Note:** weights in grams
- **Parameters:**
  - `startDate` (path, string) *(required)* — The start date(user's local calendar) of the range, inclusive. Format yyyy-MM-dd.
  - `endDate` (path, string) *(required)* — The end date(user's local calendar) of the range, inclusive. Format yyyy-MM-dd.
  - `includeAll` (query, boolean, default `False`) — If true, include all weight entries for each day in the range. If false, only include the latest weight entry for each day.
- **Response** (object):
  - `dailyWeightSummaries`: array<DailyWeightSummary>
  - `totalAverage`: WeightAverageDTO
  - `previousDateWeight`: DateWeightDTO
  - `nextDateWeight`: DateWeightDTO


## wellness-service

### `GET /wellness-service/wellness/bodyBattery/reports/daily`

Returns daily Body Battery reports for a date range, up to a maximum of 31 days.

- **CLI:** `bodybattery` · **Client:** `body_battery_daily(s,e)`
- **Note:** max 31 days (auto-chunked)
- **Parameters:**
  - `startDate` (query, string)
  - `endDate` (query, string)
  - `chunks` (query, integer) — Number of time intervals each day is divided into; the response includes the lowest and highest Body Battery readings from each interval.
- **Response** (list of objects):
  - `date`: string
  - `charged`: integer
  - `drained`: integer
  - `startTimestampGMT`: string
  - `endTimestampGMT`: string
  - `startTimestampLocal`: string
  - `endTimestampLocal`: string
  - `bodyBatteryValuesArray`: array<array>
  - `bodyBatteryValueDescriptorDTOList`: array<BodyBatteryValueDescriptorDTO>
  - `bodyBatteryDynamicFeedbackEvent`: BodyBatteryDynamicFeedbackEventDTO
  - `bodyBatteryActivityEvent`: array<BodyBatteryActivityEventDTO>
  - `endOfDayBodyBatteryDynamicFeedbackEvent`: BodyBatteryDynamicFeedbackEventDTO

### `GET /wellness-service/wellness/daily/spo2acclimation/{calendarDate}`

Returns daily SpO2 readings data for a given calendar date.

- **CLI:** `spo2` · **Client:** `spo2_acclimation(date)`
- **Parameters:**
  - `calendarDate` (path, string) *(required)*
- **Response** (object):
  - `userProfilePK`: integer
  - `calendarDate`: string
  - `startTimestampGMT`: string
  - `endTimestampGMT`: string
  - `startTimestampLocal`: string
  - `endTimestampLocal`: string
  - `sleepStartTimestampGMT`: string
  - `sleepEndTimestampGMT`: string
  - `sleepStartTimestampLocal`: string
  - `sleepEndTimestampLocal`: string
  - `tomorrowSleepStartTimestampGMT`: string
  - `tomorrowSleepEndTimestampGMT`: string
  - `tomorrowSleepStartTimestampLocal`: string
  - `tomorrowSleepEndTimestampLocal`: string
  - `averageSpO2`: number
  - `lowestSpO2`: integer
  - `lastSevenDaysAvgSpO2`: number
  - `latestSpO2`: integer
  - `latestSpO2TimestampGMT`: string
  - `latestSpO2TimestampLocal`: string
  - `avgSleepSpO2`: number
  - `avgTomorrowSleepSpO2`: number
  - `spO2SingleValuesDescriptorList`: array<SPO2ValueDescriptorDTO>
  - `spO2SingleValues`: array<array>
  - `spO2HourlyAveragesDescriptorList`: array<SPO2AcclimationValueDescriptorDTO>
  - `spO2HourlyAverages`: array<array>
  - `monitoringEnvironmentValuesDescriptorList`: array<MonitoringEnvironmentValueDescriptorDTO>
  - `monitoringEnvironmentValues`: array<array>

### `GET /wellness-service/wellness/dailyHeartRate`

Returns daily heart rate data for a given date.

- **CLI:** `heartrate` · **Client:** `daily_heart_rate(date)`
- **Parameters:**
  - `date` (query, string)
- **Response** (object):
  - `userProfilePK`: integer
  - `calendarDate`: ConnectDate
  - `startTimestampGMT`: ConnectTimestamp
  - `endTimestampGMT`: ConnectTimestamp
  - `startTimestampLocal`: ConnectTimestamp
  - `endTimestampLocal`: ConnectTimestamp
  - `maxHeartRate`: integer
  - `minHeartRate`: integer
  - `restingHeartRate`: integer
  - `lastSevenDaysAvgRestingHeartRate`: integer
  - `abnormalHrThresholdValue`: integer
  - `lowAbnormalHrThresholdValue`: integer
  - `abnormalHRValuesArray`: array<array>
  - `heartRateValueDescriptors`: array<HeartRateValueDescriptorDTO>
  - `heartRateValues`: array<array>


## wellnessactivity-service

### `GET /wellnessactivity-service/activity/summary/range/{fromDate}/{untilDate}`

Returns a list of wellness activity summaries for the given date range. The fromDate and untilDate are inclusive.

- **CLI:** `wellnessactivity` · **Client:** `wellness_activities(s,e)`
- **Parameters:**
  - `fromDate` (path, string) *(required)*
  - `untilDate` (path, string) *(required)*
- **Response** (list of objects):
  - `userProfilePk`: integer
  - `activityUuid`: GarminUUID
  - `calendarDate`: ConnectDate
  - `rulePK`: integer
  - `activityName`: string
  - `notes`: string
  - `wellnessActivityType`: string
  - `startTimestampGMT`: ConnectTimestamp
  - `endTimestampGMT`: ConnectTimestamp
  - `startTimestampLocal`: ConnectTimestamp
  - `endTimestampLocal`: ConnectTimestamp
  - `summaryTypeDataList`: array<SummaryTypeDataDTO>
  - `timeInZoneList`: array<TimeInZoneDTO>
  - `deviceMetaData`: DeviceMetaDataDTO
