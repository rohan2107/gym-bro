# Energy Balance & Weight Loss Analytics

**Feature Phase**: Week 13-15 (Phase 3C)  
**Status**: Planned  
**Goal**: Science-based weight loss tracking using thermodynamics principles

---

## 🔬 Scientific Foundation

### Core Principle: Thermodynamics
- **Energy Balance** = Energy In (food) - Energy Out (TDEE)
- **3500 calories** = 1 lb of body fat
- **500 cal/day deficit** = 1 lb/week weight loss
- **Validation**: If actual weight change doesn't match predicted, data has errors

---

## 📊 System Architecture

### 1. TDEE Estimation (Adaptive Algorithm)

**Initial Estimate (Week 1-2)**:
```
Mifflin-St Jeor Equation:
BMR (males) = 10×weight(kg) + 6.25×height(cm) - 5×age + 5
BMR (females) = 10×weight(kg) + 6.25×height(cm) - 5×age - 161

TDEE = BMR × Activity Multiplier:
- Sedentary (1.2): Little/no exercise
- Light (1.375): Exercise 1-3 days/week
- Moderate (1.55): Exercise 3-5 days/week
- Active (1.725): Exercise 6-7 days/week
- Very Active (1.9): Athlete/physical job
```

**Adaptive Learning (Week 3+)**:
```python
# Calculate actual TDEE from observed data
actual_weight_change_lbs = current_weight - weight_2_weeks_ago
calories_deficit = actual_weight_change_lbs * 3500 / 14  # daily deficit
actual_TDEE = avg_calories_consumed + calories_deficit

# Smooth with moving average (prevent noise)
TDEE_estimate = 0.7 * previous_TDEE + 0.3 * actual_TDEE

# Constrain to prevent wild swings
TDEE_estimate = clamp(previous_TDEE * 0.9, TDEE_estimate, previous_TDEE * 1.1)
```

**Why Adaptive**:
- Static formulas have ±300 cal error (15-20%)
- Metabolism varies person-to-person
- Non-Exercise Activity Thermogenesis (NEAT) varies widely
- Converges to personal TDEE in 3-4 weeks

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

### 5. Data Validation & Alerts

**Discrepancy Detection**:
```python
expected_change = weekly_deficit / 3500  # lbs
actual_change = current_weight - weight_last_week

error_pct = abs(expected - actual) / abs(expected)

if error_pct > 0.2:  # >20% off
    if actual < expected:
        # Losing faster than expected
        possible_causes = [
            "Underreporting food intake",
            "TDEE estimate too low",
            "Increased activity not logged"
        ]
    else:
        # Losing slower than expected
        possible_causes = [
            "Overreporting food portions",
            "TDEE estimate too high",
            "Water retention (temporary)"
        ]
    
    alert_user(possible_causes)
```

**Confidence Score**:
```python
# Data completeness
days_logged = count(food_logs in week)
workouts_logged = count(workouts in week)
weights_logged = count(weight_checkins in week)

completeness = (days_logged + workouts_logged + weights_logged) / 21
confidence = completeness * (1 - error_pct)

if confidence < 0.5:
    warning = "Low confidence - log more data for accurate predictions"
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
│  ░░░░░░░░░░░░░ 2,100 cal (TDEE)            │
│  ▓ 320 cal (Workout)                        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  Deficit: 578 calories ✓                    │
│  Expected: -0.08 lbs today                  │
└─────────────────────────────────────────────┘
```

**Middle Section - Weekly Trend**:
```
┌─────────────────────────────────────────────┐
│  This Week (Jan 6 - Jan 13)                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  Avg Daily Deficit: 485 cal                 │
│  Expected Loss: 0.97 lbs                    │
│  Actual Loss: 1.2 lbs                       │
│  Confidence: 87% ✓                          │
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

**Discrepancy Banner**:
```
┌─────────────────────────────────────────────┐
│  ⚠️ Data Mismatch Detected                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  You lost 1.8 lbs this week, but your       │
│  energy balance suggests 1.0 lb.            │
│                                             │
│  Possible causes:                           │
│  • Underreporting food intake               │
│  • TDEE estimate too low                    │
│  • Increased activity not logged            │
│                                             │
│  [Review Food Logs] [Adjust TDEE]           │
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

**Validation**:
- [ ] Predicted weight loss within ±10% of actual (after 4 weeks of data)
- [ ] TDEE estimate converges within ±5% by week 4
- [ ] Strong import successfully parses 95%+ of workouts
- [ ] LLM calorie estimates within ±20% of measured values (heart rate monitor)

**User Experience**:
- [ ] Setup wizard completed in <3 minutes
- [ ] Energy balance dashboard loads in <1 second
- [ ] Import Strong CSV in <30 seconds (100 workouts)
- [ ] Discrepancy alerts are actionable (not false positives)

**Portfolio Showcase**:
- [ ] Demonstrate adaptive algorithm (before/after TDEE adjustment)
- [ ] Show data validation catching tracking errors
- [ ] Explain thermodynamics principles in interview
- [ ] Analytics dashboard screenshot for resume/portfolio

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
- **Adaptive algorithms**: Self-correcting systems that learn from data
- **Data validation**: Detecting anomalies and providing feedback
- **Domain knowledge**: Applied thermodynamics and nutrition science
- **LLM integration**: Using AI for domain-specific estimation tasks
- **CSV parsing**: Handling external data imports
- **User feedback loops**: Helping users correct their own tracking errors

**Portfolio value**: This is the differentiator. Shows you can build intelligent systems that validate themselves and help users improve data quality.
