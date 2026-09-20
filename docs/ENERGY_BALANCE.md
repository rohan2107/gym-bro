# Energy balance and weight-trend analytics

**Status**: design for [M3.1](ROADMAP.md#m31-analytics-endpoints). Not implemented.

Estimate energy expenditure, compare logged intake against it, and check whether the observed
weight trend is consistent with the result. The output is a diagnosis that says what is
inconsistent and how confident it is, never a prescription.

## Scope

There is **no dashboard**. These are backend endpoints, and their main consumer is the agent
in [Phase 3](ROADMAP.md#phase-3-agents-and-tools), which calls them as tools to answer
questions such as "am I actually in a deficit this week?" over a real schema with per-user
isolation.

| In scope | Deferred |
|---|---|
| Baseline TDEE from a standard equation | Workout calorie estimation (METs, model-based) |
| Adaptive TDEE from observed data | Strong CSV import |
| Daily and rolling energy balance | Apple Health, Strava, Garmin integration |
| Consistency analysis of intake, expenditure and weight | Body-composition tracking |
| Data-completeness reporting | Any UI |

## Principles

- **Energy balance is a constraint, not a prediction.** Energy in minus energy out, with about
  7,700 kcal per kg of fat mass, is a *long-run* equivalence over weeks. It does not predict
  daily weight.
- **Weight is a noisy proxy.** Day-to-day movement is dominated by water, glycogen and gut
  content, so short-term fluctuation is ignored, not explained.
- **Diagnose, do not correct.** When trend and balance disagree over a long enough window, say
  which assumption is most suspect. Never silently rewrite a user's intake or TDEE.
- **Acknowledge insufficient data.** Below a minimum amount of logging the honest answer is
  "not enough data".

The app stores weight in kilograms, so this design uses kilograms throughout.

## Calculations

### Baseline TDEE

Mifflin-St Jeor resting rate, scaled by an activity multiplier:

```
BMR (male)   = 10 x weight_kg + 6.25 x height_cm - 5 x age + 5
BMR (female) = 10 x weight_kg + 6.25 x height_cm - 5 x age - 161
TDEE_prior   = BMR x activity   (sedentary 1.2, light 1.375, moderate 1.55,
                                 active 1.725, very active 1.9)
```

Static equations carry roughly ±300 kcal of error, so this is a prior, not an answer.

### Daily and rolling balance

```
balance_day        = calories_in - TDEE_estimate
expected_change_kg = sum(balance over the window) / 7700
```

### Adaptive TDEE

Once enough data exists, TDEE is re-estimated from the observed weight trend and intake over a
multi-week window, smoothed so a single week cannot move it much. The smoothing method and
window are to be fixed in the M3.1 design and validated on synthetic data (see Testing).

### Consistency analysis

Over a window of at least three to four weeks, compare the expected change with the smoothed
observed change. If they diverge beyond a threshold, rank explanations:

1. Systematic intake under- or over-reporting
2. Drift in expenditure (activity or non-exercise movement changed)
3. Weight noise (water retention, measurement variance)
4. A combination of moderate errors

The output is a ranked list with a coarse confidence (`insufficient_data`, `low`, `moderate`,
`high`) and an action of `review`, never `correct`.

The earlier draft of this design named per-hypothesis likelihood functions without defining
them. **They are unspecified.** M3.1 begins by choosing simple, explicit, rule-based scoring
that can be tested against known ground truth, rather than implying a statistical model that
does not exist.

### Data completeness

A minimum share of days with intake logged and a minimum number of weigh-ins in the window.
Below it the response is `incomplete_data` with a message asking for more consistent logging.

## Data model

Additions use integer keys referencing `user.id`, matching the existing schema. The earlier
draft used text user ids, which would not join.

| Table | Purpose | Key fields |
|---|---|---|
| `user_profile` | One per user | `user_id`, age, sex, `height_cm`, activity level, goal |
| `tdee_estimate` | Time series | `user_id`, date, `tdee_kcal`, method (`prior` or `adaptive`), confidence |

Daily balance is computed on demand from food logs and estimates rather than stored, to avoid
a second source of truth that can drift. Add materialisation only if measurement shows a need.

## Endpoints

All are authenticated and scoped to the calling user.

| Method | Path | Returns |
|---|---|---|
| `POST` | `/analytics/tdee/setup` | Initial TDEE from profile inputs |
| `GET` | `/analytics/tdee` | Current estimate and history |
| `GET` | `/analytics/energy-balance?date=&range=` | Balance over a date range |
| `GET` | `/analytics/validate?weeks=` | The consistency analysis |

## As agent tools

Each endpoint is exposed as a tool whose `user_id` comes from the authenticated session and
is never a model-supplied argument. All are read-only apart from profile setup, which is a
write and therefore needs confirmation under [M3.3](ROADMAP.md#m33-trajectory-evaluation-and-safe-mutation).

## Testing

The expected answer must be known, so tests use **synthetic trajectories with planted ground
truth**: generate a user with a true TDEE and a known intake bias, produce noisy weights, and
assert the analysis flags the planted cause and reports low confidence when the data is thin.
Property tests check invariants, such as balance summing correctly and expected change
reversing sign with the balance.

## Non-goals

- Predicting daily weight
- Automatically adjusting the user's targets or logged values
- Modelling hormones, metabolic adaptation or body composition
- Requiring perfect logging to be useful
