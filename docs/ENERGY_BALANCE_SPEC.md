# Energy Balance & Weight Loss Analytics

**Feature Phase**: Week 13-15 (Phase 3C)  
**Status**: Planned  
**Goal**: Science-based weight loss tracking using thermodynamics principles

---

## 🔬 Scientific Foundation

### Core Principle: Thermodynamics as Invariant
- **Energy Balance** = Energy In (food) - Energy Out (TDEE)
- **~3500 kcal/lb** (~7700 kcal/kg) of fat mass as **long-term energy equivalence**
  - Valid for cumulative energy imbalance over weeks
  - **Not** a short-term weight prediction model
- **Weight is a noisy proxy**: Short-term fluctuations dominated by water, glycogen, and gut content
- **Probabilistic Diagnosis**: When observed weight trajectories diverge from expected energy balance over sufficient time horizons (multi-week), the system probabilistically evaluates which assumptions (intake tracking, expenditure estimation, measurement noise, or physiological masking) are most inconsistent with the data

---

## 📊 System Architecture

### 1. TDEE Estimation (Latent Variable Inference)

**Initial Prior (Week 1-2)**:
```
Mifflin-St Jeor Equation (starting estimate):
BMR (males) = 10×weight(kg) + 6.25×height(cm) - 5×age + 5
BMR (females) = 10×weight(kg) + 6.25×height(cm) - 5×age - 161

TDEE_prior = BMR × Activity Multiplier:
- Sedentary (1.2): Little/no exercise
- Light (1.375): Exercise 1-3 days/week
- Moderate (1.55): Exercise 3-5 days/week
- Active (1.725): Exercise 6-7 days/week
- Very Active (1.9): Athlete/physical job
```

**Latent Variable Framework (Multi-Week Analysis)**:
```python
# Three latent variables contributing to divergence:
# 1. Intake bias (under/over-reporting)
# 2. Expenditure estimation error
# 3. Weight noise (water, glycogen, measurement)

# Use smoothed, cumulative signals (minimum 3-4 weeks)
smoothed_weight_change = moving_avg(weights, window=14) - moving_avg(weights_4wks_ago, window=14)
cumulative_energy_balance = sum(daily_balance for 28 days)

# Expected fat mass change (long-term equivalence)
expected_fat_change_lbs = cumulative_energy_balance / 3500

# Divergence triggers probabilistic evaluation, NOT automatic correction
divergence = smoothed_weight_change - expected_fat_change_lbs

# TDEE is one possible explanation, not the primary correction target
if abs(divergence) > threshold:
    evaluate_hypotheses([intake_bias, tdee_error, noise, combined])
```

**Why Latent Variables**:
- Static formulas have ±300 cal error (15-20%)
- Intake tracking has systematic bias (typically 10-30% underreporting)
- Weight reflects multiple physiological systems, not just fat
- System diagnoses inconsistency, does not claim deterministic correction

---

### 2. Workout Calorie Burn Estimation

**Three-Tiered Approach**:

| Method | Use Case | Accuracy | Cost |
|--------|----------|----------|------|
| **User Override** | User has HR monitor data | 100% | $0 |
| **LLM Estimation** | Complex weightlifting | 85% | $0.01/workout |
| **MET Database** | Standard cardio | 70% | $0 |

**LLM Prompt (GPT-4/Claude)**:
```
You are a fitness expert estimating calorie burn.

User Profile:
- Age: 30, Gender: Male, Weight: 180 lbs, Height: 5'10"

Workout:
- Exercise: Bench Press
- Sets: 3, Reps: 10, Weight: 185 lbs
- Duration: 30 minutes (including rest)

Estimate total calories burned. Respond with JSON:
{
  "calories": <number>,
  "confidence": <0-100>,
  "reasoning": "<brief explanation>"
}
```

**MET Database (Fallback)**:
```python
# METs (Metabolic Equivalents) from Compendium of Physical Activities
MET_values = {
    "running_6mph": 9.8,
    "cycling_moderate": 5.8,
    "weightlifting_vigorous": 6.0,
    "walking_3mph": 3.5
}

calories_per_hour = MET * weight_kg
calories_burned = calories_per_hour * duration_hours
```

---

### 3. Strong App Integration

**Import Flow**:
1. User exports CSV from Strong app
2. Upload CSV via UI
3. Backend parses workout data
4. For each exercise:
   - Check cache for common exercises
   - If not cached → LLM estimation
   - Store calorie estimate with workout
5. User reviews estimates, can override
6. Save to database as regular workouts

**Strong CSV Format**:
```csv
Date,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,Notes
2026-01-13,Bench Press,1,185,10,,,
2026-01-13,Bench Press,2,185,10,,,
2026-01-13,Bench Press,3,185,8,,,
```

**Caching Strategy**:
- Cache key: `exercise_name + sets + reps + weight + user_weight_bracket`
- TTL: 30 days
- Reduces LLM API calls by ~80% after first month

---

### 4. Energy Balance Calculation

**Daily Calculation**:
```python
energy_in = sum(food_log.calories for food_log in day)
energy_out = TDEE + workout_calories_burned
balance = energy_in - energy_out

if balance < 0:
    status = "deficit"  # losing weight
elif balance > 0:
    status = "surplus"  # gaining weight
else:
    status = "maintenance"
```

**Expected Weight Change**:
```python
weekly_deficit = sum(daily_balance for day in week)
expected_weight_change_lbs = weekly_deficit / 3500
```

---

### 5. Probabilistic Consistency Analysis

**Time Horizon Requirements**:
- **Analysis window**: Minimum 3-4 weeks of data
- **Daily values**: Diagnostic inputs, not evaluative outputs
- **Comparison surface**: Cumulative energy balance vs smoothed weight trend
- Short-term weight fluctuations (±2-4 lbs) are physiologically normal and ignored

**Multi-Hypothesis Evaluation**:
```python
# Require sufficient data (minimum 3-4 weeks)
if weeks_of_data < 3:
    return {"status": "insufficient_data", "confidence": "low"}

# Smooth signals to remove noise
smoothed_weight_trend = exponential_moving_avg(weights, alpha=0.3)
cumulative_deficit = sum(daily_energy_balance for 28 days)

# Expected vs observed (long-term)
expected_fat_loss_lbs = cumulative_deficit / 3500
observed_weight_change = smoothed_weight_trend[-1] - smoothed_weight_trend[-28]

divergence = observed_weight_change - expected_fat_loss_lbs

# Evaluate hypotheses (ranked by likelihood given data)
hypotheses = [
    {
        "explanation": "Intake underreporting",
        "likelihood": calculate_intake_bias_likelihood(divergence, tracking_patterns),
        "evidence": "Typical systematic bias in food logging"
    },
    {
        "explanation": "TDEE estimate drift",
        "likelihood": calculate_tdee_error_likelihood(divergence, activity_changes),
        "evidence": "Activity level or NEAT may have changed"
    },
    {
        "explanation": "Temporary physiological masking",
        "likelihood": calculate_noise_likelihood(divergence, weight_variance),
        "evidence": "Water retention, hormonal cycle, or measurement variance"
    },
    {
        "explanation": "Combined moderate errors",
        "likelihood": calculate_combined_likelihood(divergence),
        "evidence": "Multiple small biases compounding"
    }
]

ranked_hypotheses = sort_by_likelihood(hypotheses)

if max_likelihood < 0.6:
    confidence_level = "low - continue logging"
elif max_likelihood < 0.8:
    confidence_level = "moderate - review suggested areas"
else:
    confidence_level = "high - likely explanation identified"

return {
    "hypotheses": ranked_hypotheses,
    "confidence": confidence_level,
    "action": "review_and_consider"  # never "correct" or "fix"
}
```

**Data Completeness Score**:
```python
# Minimum viable data for meaningful analysis
min_days_logged = 20 / 28  # ~70% of days
min_weights = 4 / 4  # weekly weigh-ins

completeness = (
    (days_logged / 28) * 0.6 +
    (weights_logged / 4) * 0.4
)

if completeness < 0.7:
    return {"status": "incomplete_data", "message": "Log more consistently for insights"}
```

---

## 🎨 UI/UX Design

### Analytics Dashboard (`/analytics`)

**Top Section - Current Status**:
```
┌─────────────────────────────────────────────┐
│  Energy Balance - Today                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  ▓▓▓▓▓▓▓▓▓▓ 1,842 cal  (Food In)           │
│  ░░░░░░░░░░░░░ 2,100 cal (TDEE Est.)       │
│  ▓ 320 cal (Workout)                        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  Today's Deficit: 578 calories              │
│                                             │
│  Week Total: 3,346 cal deficit              │
│  (contributes ~1.0 lb to long-term trend)   │
└─────────────────────────────────────────────┘
```

**Middle Section - Multi-Week Trend** (minimum 4 weeks data):
```
┌─────────────────────────────────────────────┐
│  Last 4 Weeks (Dec 16 - Jan 13)             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  Avg Daily Deficit: 485 cal                 │
│  Cumulative Deficit: 13,580 cal             │
│  Expected Fat Loss: 3.9 lbs                 │
│  Smoothed Weight Change: 4.2 lbs            │
│  Consistency: High ✓                        │
│                                             │
│  Note: Short-term fluctuations normal       │
└─────────────────────────────────────────────┘
```

**Bottom Section - Graph**:
- Line chart: Expected vs Actual weight (last 12 weeks)
- Bar chart: Daily energy balance (last 30 days)

---

### TDEE Setup Wizard (First Run)

**Step 1 - Basic Info**:
- Age (number input)
- Gender (radio: Male/Female)
- Height (feet/inches)
- Current Weight (lbs)

**Step 2 - Activity Level**:
- Sedentary (desk job, no exercise)
- Light (exercise 1-3 days/week)
- Moderate (exercise 3-5 days/week)
- Active (exercise 6-7 days/week)
- Very Active (athlete/physical job)

**Step 3 - Goal**:
- Lose weight (select rate: 0.5, 1, 1.5, 2 lbs/week)
- Maintain weight
- Gain weight (muscle building)

**Result**:
```
Your Estimated TDEE: 2,100 calories/day

To lose 1 lb/week, eat: 1,600 calories/day

Note: This is an estimate. We'll refine it based on 
your actual results over the next 2-3 weeks.
```

---

### Import Strong Workouts

**Upload Screen**:
```
┌─────────────────────────────────────────────┐
│  Import Workouts from Strong App            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  1. Export CSV from Strong app              │
│  2. Upload file below                       │
│  3. Review estimates                        │
│  4. Confirm import                          │
│                                             │
│  [📁 Choose File] strong_export.csv         │
│                                             │
│  [Upload & Process]                         │
└─────────────────────────────────────────────┘
```

**Review Screen**:
```
┌─────────────────────────────────────────────┐
│  Review Imported Workouts                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  Jan 13, 2026 - Upper Body                  │
│  ▸ Bench Press (3x10 @ 185 lbs)             │
│    Est. Calories: 95 ✏️                     │
│  ▸ Rows (3x12 @ 135 lbs)                    │
│    Est. Calories: 72 ✏️                     │
│  ▸ Shoulder Press (3x10 @ 95 lbs)           │
│    Est. Calories: 68 ✏️                     │
│                                             │
│  Total Workout: 235 calories                │
│                                             │
│  [Confirm Import] [Cancel]                  │
└─────────────────────────────────────────────┘
```

---

### Data Validation Alerts

**Consistency Analysis Banner**:
```
┌─────────────────────────────────────────────┐
│  💡 Insight: Trajectory Divergence           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  Over the last 4 weeks, your weight trend   │
│  diverges from energy balance by ~1.2 lbs.  │
│                                             │
│  Likely explanations (ranked):              │
│  • 68% - Intake tracking drift              │
│  • 22% - Activity level increase            │
│  • 10% - Temporary water loss               │
│                                             │
│  Suggested review areas:                    │
│  • Portion sizes in recent logs             │
│  • Unlogged snacks or drinks                │
│                                             │
│  [Review Recent Logs] [Dismiss]             │
└─────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema

### New Tables

**user_profiles** (one-per-user):
```sql
CREATE TABLE user_profiles (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    age INTEGER NOT NULL,
    gender TEXT CHECK(gender IN ('male', 'female')),
    height_cm REAL NOT NULL,
    activity_level TEXT CHECK(activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active')),
    goal TEXT CHECK(goal IN ('lose', 'maintain', 'gain')),
    goal_rate_lbs_per_week REAL,  -- e.g., 1.0 for 1 lb/week loss
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**tdee_estimates** (time-series):
```sql
CREATE TABLE tdee_estimates (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    tdee_calories INTEGER NOT NULL,
    method TEXT CHECK(method IN ('mifflin', 'adaptive')),
    confidence REAL,  -- 0-1
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);
```

**energy_balance** (calculated daily):
```sql
CREATE TABLE energy_balance (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    calories_in INTEGER NOT NULL,
    calories_out INTEGER NOT NULL,  -- TDEE + workouts
    balance INTEGER NOT NULL,  -- in - out
    expected_weight_change_lbs REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);
```

**workout_calorie_cache**:
```sql
CREATE TABLE workout_calorie_cache (
    id INTEGER PRIMARY KEY,
    exercise_name TEXT NOT NULL,
    user_weight_bracket TEXT NOT NULL,  -- e.g., "170-180"
    sets INTEGER,
    reps INTEGER,
    weight_lbs REAL,
    calories_estimate INTEGER NOT NULL,
    source TEXT CHECK(source IN ('llm', 'met', 'user')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(exercise_name, user_weight_bracket, sets, reps, weight_lbs)
);
```

---

## 🔌 API Endpoints

### Analytics

**GET /analytics/tdee**
- Returns: Current TDEE estimate + history

**POST /analytics/tdee/setup**
- Body: `{ age, gender, height_cm, activity_level, goal, goal_rate }`
- Returns: Initial TDEE calculation

**GET /analytics/energy-balance?date={date}&range={days}**
- Returns: Energy balance for date range

**GET /analytics/validate?weeks={n}**
- Returns: Discrepancy analysis for last n weeks

### Imports

**POST /imports/strong**
- Body: `multipart/form-data` (CSV file)
- Returns: Parsed workouts with calorie estimates

**GET /imports/strong/preview/{import_id}**
- Returns: Preview of import before confirmation

**POST /imports/strong/confirm/{import_id}**
- Saves imported workouts to database

### AI Services

**POST /ai/estimate-workout-calories**
- Body: `{ exercise_name, sets, reps, weight_lbs, duration_min, user_profile }`
- Returns: `{ calories, confidence, reasoning }`

---

## 💰 Cost Estimate

**LLM API Usage** (GPT-4):
- ~$0.01 per workout estimate
- Avg user: 3 workouts/week
- Monthly: ~12 estimates = **$0.12/user/month**
- Cache reduces by 80% after month 1 → **$0.02/user/month**

**Total Phase 3C Cost**: ~$0.50/month (includes AI meal photos + workout estimates)

---

## 🎯 Success Metrics

**System Integrity**:
- [ ] Consistency analysis requires minimum 3-4 weeks of data (prevents noise amplification)
- [ ] Weight smoothing filters out physiological noise (±2-4 lb swings ignored)
- [ ] Strong import successfully parses 95%+ of workouts
- [ ] Multi-hypothesis evaluation provides ranked explanations
- [ ] System gracefully degrades with incomplete data

**User Experience**:
- [ ] Setup wizard completed in <3 minutes
- [ ] Energy balance dashboard loads in <1 second
- [ ] Import Strong CSV in <30 seconds (100 workouts)
- [ ] Insights are diagnostic and actionable (not accusatory)
- [ ] Analytics remain optional and non-blocking to core app usage

**Diagnostic Quality** (qualitative validation):
- [ ] Hypothesis rankings align with known tracking patterns
- [ ] System acknowledges uncertainty when data insufficient
- [ ] Language emphasizes review and consideration, not correction

**Portfolio Showcase**:
- [ ] Demonstrate adaptive algorithm (before/after TDEE adjustment)
- [ ] Show data validation catching tracking errors
- [ ] Explain thermodynamics principles in interview
- [ ] Analytics dashboard screenshot for resume/portfolio

---

## 🏗️ System Design Principles

### Constraints That Preserve Integrity

1. **Minimum Time Horizon**: No analysis with <3 weeks of data
   - Prevents noise amplification
   - Ensures physiological signal dominates measurement noise

2. **Thermodynamics as Invariant**: Energy balance is never "wrong"
   - Weight divergence triggers hypothesis evaluation
   - System never claims to "know" which variable is incorrect

3. **Probabilistic Output**: All insights include uncertainty
   - Ranked explanations, not singular answers
   - Confidence levels communicated clearly

4. **Optional and Non-Blocking**: Analytics degrade gracefully
   - Core app (logging, workouts) remains functional
   - Insights appear when sufficient data available
   - Missing data shows guidance, not errors

5. **Diagnostic, Not Prescriptive**: Language matters
   - "Consider reviewing" vs "You are wrong"
   - "Likely explanation" vs "The problem is"
   - "Insufficient data" vs "Invalid data"

### What This System Does NOT Do

- ❌ Claim to predict daily weight changes
- ❌ Automatically "correct" TDEE or intake values
- ❌ Blame users for normal physiological variance
- ❌ Provide deterministic answers to multi-factorial questions
- ❌ Model hormones, metabolism adaptation, or body composition
- ❌ Require perfect logging to provide value

### What This System DOES Do

- ✅ Highlight inconsistencies over multi-week horizons
- ✅ Suggest probable areas for user review
- ✅ Acknowledge uncertainty and noise
- ✅ Respect thermodynamics as a constraint
- ✅ Provide value with incomplete data
- ✅ Maintain academic and scientific defensibility

---

## 📚 Future Enhancements

**Phase 4+ (Post-MVP)**:
- Apple Health integration (requires Swift app)
- Strava/Garmin/Fitbit API imports
- MyFitnessPal food database (better calorie estimates)
- Body composition tracking (lean mass vs fat mass)
- Adaptive macro targets (protein/carbs/fat optimization)
- Metabolic adaptation detection (adaptive thermogenesis)

---

## 🎓 Learning Outcomes

By building this feature, you'll learn:
- **Probabilistic inference**: Multi-hypothesis evaluation with uncertainty quantification
- **Latent variable modeling**: Reasoning about unmeasured factors (intake bias, TDEE drift)
- **Constraint-aware systems**: Treating thermodynamics as a hard invariant
- **Signal processing**: Smoothing noisy measurements to extract trends
- **Domain knowledge**: Applied thermodynamics and physiological confounders
- **LLM integration**: Using AI for domain-specific estimation tasks (with uncertainty)
- **Diagnostic design**: Building systems that explain, not prescribe
- **Graceful degradation**: Optional analytics that remain valuable with incomplete data

**Portfolio value**: This differentiates through **scientific rigor and restraint**. Demonstrates ability to:
- Build systems that acknowledge uncertainty
- Apply invariant-preserving inference
- Design diagnostic tools that avoid false confidence
- Balance product pragmatism with academic defensibility
