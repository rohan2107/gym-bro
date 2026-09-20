# Implementation Roadmap

**Last Updated**: September 16, 2026  
**Current Status**: Phase 4.3 Complete — AI photo logging shipped end to end

> Development after Phase 4.3 is planned in the [AI Roadmap](AI_ROADMAP.md), which supersedes
> the upcoming phases below. Phase 5 is repurposed there: the energy-balance endpoints are kept
> as agent tools, the dashboard is dropped.

---

## Completed Phases

### Phase 1: Mobile PWA (January 2026) ✅
- Mobile-first responsive design with bottom navigation
- Full CRUD for check-ins, meals, workouts
- Offline support with service worker
- Production deployment (Vercel + PostgreSQL on Neon)

### Phase 2: Authentication (February 18, 2026) ✅
- Google OAuth 2.0 with JWT (httpOnly cookies)
- Multi-user support with data isolation
- Protected routes and secure sessions

**Details**: [OAuth Setup Guide](GOOGLE_OAUTH_SETUP.md)

### Phase 3: Testing & CI/CD (February 18, 2026) ✅
- Automated test suite (47 backend + 27 frontend at phase completion)
- GitHub Actions pipeline with 7 parallel required quality gates
- Alembic database migrations configured

### Phase 4: AI Meal Photo Logging (February 21-24, 2026) ✅

#### Phase 4.1: Infrastructure Setup ✅
- Backend service layer (Vision, Nutrition, RateLimiter, FoodMapping)
- Database schema updates (photo_count, last_photo_date)
- API setup documentation

#### Phase 4.2: Photo Endpoint & Production Readiness ✅
- Photo upload endpoint with AI food detection
- Atomic rate limiting (race condition fix)
- 133 backend tests passing, 84% coverage
- Authorization header support (Bearer token + cookie)
- Complete code quality improvements (14/14 PR review fixes)

#### Phase 4.3: Frontend & Real Vision Integration ✅ (September 16, 2026)

Completed as Phase 0 of the [AI Roadmap](AI_ROADMAP.md), which also cleared the defects found
in the September 2026 audit.

- Real Google Cloud Vision integration (REST `images:annotate` with an API key via `httpx`,
  replacing a stub that always returned a hardcoded `"pizza"`)
- Generic-label filtering, deduplication and ranking before USDA lookup
- `PhotoCapture` (native camera on mobile, file picker on desktop, quota indicator) and
  `MealReview` (every predicted value editable, per-100g caveat stated)
- Graceful fallback: failures stay local to the photo control, manual entry always available
- Fixed: `pillow` missing from the production requirements (the endpoint 500'd in production
  while CI was green), requirements drift between the two files, a placeholder user seeded into
  production on every cold start, `create_all()` competing with Alembic for schema ownership,
  CORS admitting the whole `vercel.app` namespace, and an unpinned ruff breaking the lint job
- 216 tests (166 backend, 50 frontend), 85% backend coverage

**Status**: Implemented and unit-tested; not yet verified against the live Vision API. Set
`GOOGLE_VISION_API_KEY` and `USDA_API_KEY`, then run a real photo through it.

---

## Superseded Plans

The phases below predate the [AI Roadmap](AI_ROADMAP.md). Kept for reference.

### Phase 4.3: Frontend Implementation (superseded — delivered, see above)

**Goal**: Complete the photo logging user interface

**User Flow**:
1. User taps "📸 Photo" in Meals page → camera opens
2. Takes photo → uploads to Vercel Blob
3. Google Vision API extracts food labels
4. USDA FoodData API enriches with nutrition
5. User reviews/edits predictions → saves to food log

**Technical Implementation**:

**Backend**:
- `POST /food-logs/from-photo` — Photo upload + analysis
- Vercel Blob for photo storage
- Google Cloud Vision API for food detection
- USDA FoodData Central API for nutrition lookup
- Rate limiting (30 photos/day/user)

**Frontend**:
- `PhotoCapture.tsx` — Camera/file input component
- `MealReview.tsx` — Edit AI predictions
- Quota indicator (photos remaining)
- Graceful fallback to manual entry

**Success Criteria**:
- Photo to predictions <5 seconds
- Mobile camera support (iOS Safari, Android Chrome)
- AI confidence >70% for user trust
- Fallback to manual when API fails

**Estimated Duration**: 16 days

**Details**: [AI Meal Logging design](AI_MEAL_LOGGING.md)

---

### Phase 5: Energy Balance & Analytics (superseded — rescoped in the AI Roadmap)

The backend endpoints are kept as agent tools in AI Roadmap Phase 2. The dashboard, setup
wizard and charts are dropped.

**Goal**: TDEE tracking with weight loss validation

**Core Features**:
- **TDEE Calculator** — Mifflin-St Jeor equation with adaptive adjustment
- **Energy Balance Dashboard** — Calories in vs out with deficit tracking
- **Weight Loss Predictor** — Expected vs actual comparison
- **Validation Alerts** — Flag discrepancies (underreporting, overestimation)

**Technical Implementation**:

**Backend**:
- `POST /analytics/tdee` — Calculate TDEE from user stats
- `GET /analytics/energy-balance` — Daily deficit/surplus
- `GET /analytics/validation` — Compare predicted vs actual weight loss
- Adaptive TDEE: Adjusts weekly based on actual results

**Frontend**:
- `AnalyticsPage.tsx` — Energy balance dashboard
- `TDEESetupWizard.tsx` — One-time profile setup
- `EnergyBalanceChart.tsx` — Visual calories in/out
- Validation banners for data quality issues

**TDEE Algorithm**:
```
Week 1-2: Baseline (Mifflin-St Jeor + activity multiplier)
Week 3+:  TDEE = calories_consumed + (weight_change * 3500 / days)
          Smoothed with 2-week moving average
```

**Success Criteria**:
- TDEE adapts to actual weight loss rate
- Dashboard shows daily energy balance
- Predicted weight loss ± 10% of actual
- Actionable feedback when data doesn't match science

**Estimated Duration**: 2-3 weeks

**Details**: [Energy Balance Specification](ENERGY_BALANCE_SPEC.md)

---

## Future Enhancements

**Performance & Monitoring**:
- E2E tests with Playwright (deferred)
- Lighthouse CI integration (dropped)
- Error tracking (Sentry) — subsumed by AI Roadmap Phase 3 observability
- Performance monitoring — subsumed by AI Roadmap Phase 3

**Integrations**:
- Strong app workout import (CSV)
- Apple Health sync (iOS native)
- Strava/Garmin activity data
- MyFitnessPal food database
