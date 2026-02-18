# Gym Bro: Development Roadmap
**Updated**: February 18, 2026  
**Current Phase**: Phase 2 Complete - Google OAuth implemented, Phase 3 begins  
**Status**: Production deployed with multi-user authentication, proceeding to AI & analytics

## Project Overview

**Goal**: Production-ready fitness tracking app with Google SSO and AI meal logging

**Success Criteria**:
- [x] Deployed to production (Vercel)
- [x] Mobile-first PWA with offline support
- [x] Google OAuth working (multi-user ready) ✅ **Complete - Feb 18, 2026**
- [ ] AI meal photo logging
- [x] Portfolio-worthy code and documentation

**Tech Stack**:
- **Frontend**: React 18, TypeScript, Vite, Tailwind (PWA)
- **Backend**: FastAPI, SQLModel, Pydantic v2
- **Database**: PostgreSQL (Neon)
- **Auth**: Google OAuth 2.0 + JWT (next phase)
- **Hosting**: Vercel
- **Storage**: Vercel Blob (planned)
- **AI**: Google Cloud Vision API (planned)

---

## 📅 12-Week Sprint Plan

### **Phase 1A: Mobile UX & Polish**
**Focus**: Make it usable on YOUR phone daily  
**Status**: ✅ COMPLETE (January 19, 2026)

**Deliverables**:
- [x] Bottom navigation (tab-based UI) ✅ **Complete - Jan 13, 2026**
- [x] Responsive mobile layout (full-width, single-column on phone) ✅ **Complete**
- [x] Edit/Delete functionality for meals & workouts ✅ **Complete - Jan 13, 2026**
- [x] Date picker for check-in history ✅ **Complete - Jan 13, 2026**
- [x] Offline caching (service worker) ✅ **Complete - Jan 13, 2026**
- [x] Tested on actual phone ✅ **Complete**

**Definition of Done**: ✅ ACHIEVED
- You can log check-in, meal, workout in <10 seconds from home screen
- Works offline (logs queue, sync when online)
- Lighthouse PWA score >90 (estimated, not yet measured)
- Mobile-first responsive design complete

**Time estimate**: 2–3 weeks → **Actual: 1 week**

---

### **Phase 1B: Vercel Deployment**
**Focus**: Production infrastructure  
**Status**: ✅ COMPLETE (January 19, 2026)

**Deliverables**:
- [x] Neon PostgreSQL database created ✅ **Complete**
- [x] Frontend deployed to Vercel ✅ **Complete**
- [x] Backend deployed to Vercel Functions ✅ **Complete**
- [x] Backend API integration verified ✅ **Complete**
- [x] CORS properly configured ✅ **Complete**
- [x] Database connection pooling ✅ **Complete**
- [x] Auto-seeding for MVP ✅ **Complete**

**Definition of Done**: ✅ ACHIEVED
- App is live at https://gym-ba2oz8etc-rohan-anthonys-projects-a86489a8.vercel.app
- Backend API accessible at `/api/health`
- Data persists in PostgreSQL (Neon)
- Full CRUD operations working in production

**Cost**: $0 (all free tier) ✅ **Confirmed**

---

### Phase 2: Google OAuth Authentication ✅ COMPLETE (Feb 18, 2026)
**Status**: All deliverables implemented and tested on production

**Objective**: Replace temporary X-User-Id header with real Google OAuth authentication ✅ **ACHIEVED**

**Key Deliverables**:

**Backend** ✅ COMPLETE:
- [x] Google Cloud project + OAuth credentials
- [x] `/auth/google/login` endpoint (initiate OAuth flow)
- [x] `/auth/google/callback` endpoint (handle OAuth response)
- [x] JWT token generation and validation (7-day expiry, HS256)
- [x] Updated `get_user_id()` dependency to extract from JWT cookie
- [x] User model updates (google_id, email, display_name, picture_url)

**Frontend** ✅ COMPLETE:
- [x] Login page with "Sign in with Google" button
- [x] Auth context for managing authentication state
- [x] Protected routes (redirect to login if not authenticated)
- [x] Token storage in httpOnly cookies
- [x] Updated API client to send JWT via cookies

**Testing** ✅ COMPLETE:
- [x] Sign in with Google account
- [x] Create data (check-ins, meals, workouts)
- [x] Sign out and verify data security
- [x] Sign in as different user and verify data isolation
- [x] Tested on production (Vercel with environment variables)

**Success Criteria** ✅ **ACHIEVED**:
- [x] Multiple users can sign in with their Google accounts
- [x] Each user sees only their own data
- [x] Authentication works in production
- [x] Single callback request per OAuth flow (no duplicate requests)

**Technical Details**: See [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md) for implementation guide and [gymbro-api/app/routers/auth.py](gymbro-api/app/routers/auth.py) for code

---

### Phase 3: Testing & CI/CD Pipeline

**Goal**: Comprehensive test coverage and automated quality gates

**Testing Strategy**:

**Unit Tests (Backend)**:
- [ ] Expand pytest coverage to >80%
- [ ] Test all routers (daily-checkins, food-logs, workouts)
- [ ] Test authentication helpers and dependencies
- [ ] Test database models and validation
- [ ] Mock external dependencies (database, OAuth)

**Unit Tests (Frontend)**:
- [ ] Vitest + React Testing Library setup
- [ ] Test components (Forms, BottomNav, OfflineIndicator)
- [ ] Test utility functions (date formatting, API client)
- [ ] Test hooks and context providers
- [ ] Mock API responses

**Integration Tests**:
- [ ] API endpoint integration tests with test database
- [ ] Database transaction tests (CRUD operations)
- [ ] Authentication flow integration tests
- [ ] Error handling across layers

**E2E Tests (Playwright)**:
- [ ] Critical user flows:
  - Sign in with Google (once OAuth is live)
  - Create daily check-in
  - Log meal with full data
  - Create and edit workout
  - Offline mode (cache, sync)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile viewport testing

**CI/CD Pipeline (GitHub Actions)**:
- [ ] On pull request:
  - Run backend unit tests (pytest)
  - Run frontend unit tests (Vitest)
  - TypeScript type checking
  - Linting (ESLint, Ruff)
  - Build verification
- [ ] On merge to main:
  - All PR checks
  - Integration tests
  - Deploy to Vercel (automatic)
  - Run E2E tests against staging
  - Performance checks (Lighthouse CI)

**Performance & Monitoring**:
- [ ] Response time optimization (<200ms avg)
- [ ] Database query optimization (indexes, N+1 queries)
- [ ] Frontend bundle size optimization
- [ ] Lighthouse CI integration (PWA score >90)
- [ ] Error tracking setup (Sentry or similar)
- [ ] Performance monitoring (Vercel Analytics)

**Database Management**:
- [ ] Migration strategy (Alembic setup)
- [ ] Rollback procedures
- [ ] Seed data for testing environments
- [ ] Backup verification

**Success Criteria**:
- ✅ 80%+ backend test coverage
- ✅ 70%+ frontend test coverage
- ✅ All E2E tests passing
- ✅ CI/CD pipeline green on every merge
- ✅ Zero production errors for 1 week
- ✅ Response time <200ms P95

**Time Estimate**: 2-3 weeks

---

### Phase 4: AI Meal Photo Logging

**Goal**: Auto-log meals from photos using Google Cloud Vision API

**Flow**:
1. User captures meal photo
2. Upload to Vercel Blob
3. Backend calls Google Cloud Vision API
4. Extract food items and portions
5. Enrich with nutrition data (USDA FoodData)
6. Present estimates for user confirmation
7. Save to food log

**Key Components**:
- [ ] Photo upload (Vercel Blob integration)
- [ ] Google Cloud Vision API setup
- [ ] USDA FoodData API integration
- [ ] ML confidence thresholds
- [ ] User confirmation UI
- [ ] Photo storage and retrieval

See detailed implementation plan in later phases.

---

## Current Status Summary

**Completed**:
- ✅ Mobile-first PWA with offline support
- ✅ Full CRUD for check-ins, meals, workouts
- ✅ Production deployment on Vercel
- ✅ PostgreSQL database (Neon)

**In Progress**:
- 🔄 Google OAuth authentication (Phase 2)

**Upcoming**:
- ⏳ Testing and stability (Phase 3)
- ⏳ AI meal photo logging (Phase 4)
User confirms or adjusts
    ↓
FoodLog created with AI data
```

**Deliverables**:
- [ ] Photo upload UI (camera input)
- [ ] Backend vision endpoint: `POST /food-logs/from-photo`
- [ ] Google Cloud Vision API integration
- [ ] Calorie database lookup (USDA or similar)
- [ ] Review + confirm UI (edit predictions)
- [ ] Fallback to manual entry (if vision fails)
- [ ] Photo history (view past logged meals)

**New backend files**:
- `app/routers/vision.py` — Photo processing + rate limiting
- `app/services/nutrition.py` — Calorie lookup, macro estimation
- `app/services/rate_limiter.py` — Track API usage, enforce quotas
- Update `app/models.py` — Add photo_url to FoodLog

**Rate limiting implementation**:
- [ ] Backend: Track Vision API calls per user (daily/monthly counters)
- [ ] Backend: Return 429 Too Many Requests if quota exceeded
- [ ] Frontend: Display "X photos remaining today" in UI
- [ ] Frontend: 500ms debounce on photo capture (prevent spam)
- [ ] Fallback: Auto-switch to manual entry when quota hit
- [ ] Alerts: Email notification at 80% quota usage
- [ ] Free tier limits: 1000 requests/month (~33/day, ~1/hour personal use)

**New frontend files**:
- `components/PhotoCapture.tsx` — Camera input
- `components/MealReview.tsx` — Review AI predictions
- `pages/PhotoLogPage.tsx` — Full photo logging flow

**Testing**:
- [ ] Take photo of meal → Predictions accurate within 20%
- [ ] Edit predictions → Save correct data
- [ ] Fallback to manual → Works if photo fails
- [ ] Performance → <2s from photo to predictions
- [ ] Rate limiting → Quota counter accurate, graceful degradation
- [ ] Rate limiting → UI shows remaining photos, auto-fallback works

**Definition of Done**:
- You can log a meal by taking a photo
- Auto-filled calories/macros are reasonable (within 20%)
- Works on mobile camera
- No manual typing needed for food logs

**Portfolio impact**: ⭐⭐⭐ Very impressive feature

**New skills**:
- ✅ Computer vision API integration
- ✅ Image processing pipelines
- ✅ ML/AI model usage
- ✅ Fallback UX design
- ✅ Performance optimization

**Cost**: $0 (free tier covers ~30 photos/day)

**Time estimate**: 3–4 weeks (complex but well-documented APIs)

---

### **Phase 3C: Energy Balance & Analytics (Weeks 13–15)**
**Focus**: Weight loss science - thermodynamics-based energy balance tracking**

**Core Concept**: Track energy in vs energy out to predict and validate weight loss rates

**Deliverables**:
- [ ] TDEE (Total Daily Energy Expenditure) estimation algorithm
- [ ] Strong app workout import (CSV/API)
- [ ] LLM-powered calorie burn estimation for workouts
- [ ] Energy balance calculation (TDEE - calories consumed)
- [ ] Expected weight loss rate calculator
- [ ] Analytics dashboard showing predicted vs actual weight loss
- [ ] Discrepancy detection & user alerts

**Backend Features**:
- [ ] TDEE calculation endpoint: `POST /analytics/tdee`
  - Inputs: weight history, activity level, age, gender, height
  - Uses Mifflin-St Jeor + activity multiplier
  - Adaptive: recalculates weekly based on actual weight change
- [ ] Strong app import: `POST /workouts/import-strong`
  - Parse Strong CSV export
  - LLM call to estimate calorie burn per exercise
  - Store as workout entries
- [ ] Energy balance endpoint: `GET /analytics/energy-balance?date={date}`
  - Returns: TDEE, calories consumed, deficit/surplus, expected weight change
- [ ] Discrepancy detection: `GET /analytics/validate`
  - Compares expected vs actual weight loss
  - Flags data issues (underreporting food, overestimating TDEE)
  - Returns: confidence score, suggested corrections

**Frontend Features**:
- [ ] TDEE Setup Wizard (one-time)
  - Collects: age, gender, height, activity level
  - Calculates initial TDEE
- [ ] Energy Balance Dashboard (`/analytics`)
  - Daily energy balance chart (calories in/out)
  - Weekly deficit/surplus summary
  - Expected vs actual weight loss graph
  - Confidence indicators (data quality)
- [ ] Import Strong Workouts
  - Upload CSV button
  - Review imported workouts + calorie estimates
  - Confirm/edit before saving
- [ ] Data Validation Alerts
  - Banner when weight change doesn't match energy balance
  - Suggestions: "You're losing faster than expected - are you tracking all meals?"
  - Analytics insights: "Your TDEE may be higher than estimated"

**AI/LLM Integration (Workout Calorie Burn)**:
- [ ] Endpoint: `POST /ai/estimate-workout-calories`
  - Inputs: exercise name, sets, reps, weight, duration, user stats
  - LLM prompt: "Estimate calories burned for [exercise details]"
  - Returns: calorie estimate + confidence level
  - Fallback: MET (Metabolic Equivalent) database lookup
- [ ] Use GPT-4 or Claude for workout interpretation
- [ ] Cache common exercises to reduce API calls
- [ ] User can override estimates

**TDEE Algorithm (Adaptive)**:
- Week 1–2: Use Mifflin-St Jeor equation (baseline)
- Week 3+: Adjust based on actual weight change
  - If losing faster → increase TDEE estimate
  - If losing slower → decrease TDEE estimate
  - Formula: `TDEE_new = calories_consumed + (weight_change * 3500 / 7)`
  - Smoothed with 2-week moving average

**Analytics & Validation**:
- [ ] Calculate expected weight change from energy balance
  - 3500 calories = 1 lb of fat
  - Weekly deficit → expected lb/week loss
- [ ] Compare to actual weight measurements
- [ ] Flag discrepancies > 20%:
  - "Expected to lose 2 lbs, only lost 0.5 lb"
  - Possible causes: underreporting food, overestimating activity
- [ ] Provide actionable feedback

**Future Integrations (Deferred)**:
- ⏳ Apple Health import (requires Swift/iOS app - Phase 4+)
- ⏳ Strava integration (cycling/running calorie burn)
- ⏳ Fitbit/Garmin API (step count, heart rate)
- ⏳ MyFitnessPal food database integration

**New Backend Files**:
- `app/routers/analytics.py` — TDEE, energy balance, validation
- `app/routers/imports.py` — Strong CSV import
- `app/services/tdee_calculator.py` — Adaptive TDEE algorithm
- `app/services/llm_client.py` — GPT-4/Claude for workout analysis
- `app/models.py` — Add UserProfile (age, gender, height, activity level)

**New Frontend Files**:
- `pages/AnalyticsPage.tsx` — Energy balance dashboard
- `components/TDEESetup.tsx` — Initial TDEE wizard
- `components/EnergyBalanceChart.tsx` — Daily in/out visualization
- `components/ImportStrong.tsx` — CSV upload + review
- `components/DataValidationAlert.tsx` — Discrepancy warnings

**Definition of Done**:
- TDEE adapts to your actual weight loss rate
- Strong workouts import and get calorie estimates
- Dashboard shows daily energy balance
- App alerts you when data doesn't match science
- Expected weight loss ± 10% of actual (validation works)

**Portfolio Impact**: ⭐⭐⭐⭐ Shows deep understanding of fitness science + data validation

**New Skills**:
- ✅ Adaptive algorithms (TDEE recalculation)
- ✅ Data validation & anomaly detection
- ✅ CSV parsing & external data import
- ✅ LLM integration for domain-specific tasks
- ✅ Complex analytics calculations
- ✅ User feedback loops (correcting tracking errors)

**Cost**:
- LLM API: ~$0.01/workout estimate (GPT-4)
- Estimated: $5–10/month for active user
- Can cache common exercises to reduce costs

**Time Estimate**: 2–3 weeks

---

## 🎯 Success Milestones

| Week | Milestone | Status | Notes |
|------|-----------|--------|-------|
| 1–3 | Mobile UX done, using app daily | ⏳ | You're the first user |
| 2–3 | Deployed to Vercel | ⏳ | Live on internet |
| 4–6 | Google SSO working | ⏳ | Friends can log in |
| 7–8 | Stable + tested | ⏳ | Ready for AI |
| 9–12 | AI meal photos | ⏳ | Differentiated feature |
| 13–15 | Energy balance & analytics | ⏳ | Science-based weight loss |
| 12+ | Portfolio-ready | ⏳ | Interview talking points |

---

## 💡 Why This Order?

1. **Mobile UX first** → Immediate personal value (you use it)
2. **Deployment second** → Infrastructure ready for iteration
3. **Auth third** → Necessary before inviting friends
4. **Stabilization fourth** → Catch bugs before AI
5. **AI fifth** → Premium feature, done right

This order ensures:
- ✅ You get daily use value ASAP
- ✅ Infrastructure is proven before adding complexity
- ✅ Feedback loop is tight (dogfooding)
- ✅ Foundation is solid before differentiation
- ✅ Portfolio project is impressive by week 12

---

## 📚 Documentation (We've Created)

1. **PHASE1_PLAN.md** — This roadmap
2. **MOBILE_UI_SPEC.md** — Mobile design specifications
3. **DEPLOYMENT_GUIDE.md** — Vercel + Neon setup (step-by-step)
4. **GOOGLE_OAUTH_SETUP.md** — Google OAuth setup (step-by-step)
5. **STRATEGIC_ROADMAP.md** — High-level phases (reference)
6. **PROJECT_ASSESSMENT.md** — Risk assessment + tech evaluation

---

## 🛠️ Week-by-Week Breakdown (Detailed)

### **Week 1: Mobile UX Foundation**
- [ ] Day 1–2: Design mobile layout (bottom nav, responsive grid)
- [ ] Day 3–4: Implement bottom navigation component
- [ ] Day 5: Responsive styling (Tailwind, mobile-first)
- [ ] Days 6–7: Test on actual phone, iterate

**Commit**: "feat: mobile UI with bottom navigation"

---

### **Week 2: Mobile Features + Deployment Planning**
- [ ] Days 1–2: Edit/Delete meals & workouts (endpoints + UI)
- [ ] Days 3–4: Date picker for check-in history
- [ ] Day 5: Offline caching (service worker)
- [ ] Days 6–7: Vercel account setup, Neon database creation

**Commits**:
- "feat: edit/delete meals and workouts"
- "feat: date navigation for check-in history"
- "chore: setup Neon PostgreSQL database"

---

### **Week 3: Deploy to Vercel**
- [ ] Days 1–2: Migrate from SQLite to PostgreSQL (schema validation)
- [ ] Days 3–4: Deploy backend to Vercel Functions
- [ ] Days 5–6: Deploy frontend to Vercel
- [ ] Day 7: End-to-end production testing

**Commit**: "chore: deploy to Vercel production"

**At end of Week 3**: App is LIVE and you're using it daily! 🎉

---

### **Weeks 4–6: Google OAuth Setup**
- [ ] Days 1–2: Google Cloud project + credentials
- [ ] Days 3–4: Backend OAuth implementation
- [ ] Days 5–6: Frontend login page + auth context
- [ ] Days 7+: Testing, debugging, deployment

**Commits**:
- "feat(auth): Google OAuth 2.0 backend"
- "feat(auth): Google login frontend"
- "feat(auth): JWT token management"

**At end of Week 6**: Multi-user authentication working! 🔐

---

### **Weeks 7–8: Stabilization**
- [ ] Input validation hardening
- [ ] E2E test setup (Playwright)
- [ ] Performance optimization
- [ ] Error tracking setup
- [ ] Documentation updates

**Commits**:
- "test: add E2E tests"
- "feat: input validation"
- "chore: setup error tracking"

**At end of Week 8**: App is production-stable! 🚀

---

### **Weeks 9–12: AI Meal Photos**
- [ ] Days 1–2: Photo capture UI (camera input)
- [ ] Days 3–4: Google Cloud Vision integration
- [ ] Days 5–6: Review + confirm UI
- [ ] Days 7+: Testing, optimization, deployment

**Commits**:
- "feat: meal photo capture"
- "feat: Google Vision API integration"
- "feat: AI meal prediction + review"

**At end of Week 12**: AI feature complete! 🤖📸

---

## 🎓 Skills You'll Have

By completing this project, you'll have:

### Backend Skills
- ✅ FastAPI (async Python web framework)
- ✅ SQLModel + SQLAlchemy (ORM + type validation)
- ✅ PostgreSQL (relational database)
- ✅ API design (RESTful endpoints)
- ✅ Authentication (OAuth 2.0, JWT)
- ✅ Error handling & validation
- ✅ Testing (pytest)

### Frontend Skills
- ✅ React 18 (hooks, context, state management)
- ✅ TypeScript (type safety)
- ✅ Tailwind CSS (responsive design)
- ✅ PWA (service workers, offline support)
- ✅ Authentication flows (OAuth, JWT)
- ✅ Component architecture

### DevOps/Cloud Skills
- ✅ Vercel deployment (serverless)
- ✅ PostgreSQL (cloud database)
- ✅ Google Cloud (OAuth, Vision API)
- ✅ CI/CD (GitHub → Vercel)
- ✅ Environment configuration
- ✅ Production debugging

### AI/ML Skills
- ✅ Vision API integration
- ✅ Image processing pipelines
- ✅ ML model API usage
- ✅ Fallback design patterns

### Soft Skills
- ✅ Full-stack development
- ✅ System architecture
- ✅ Documentation
- ✅ Testing & QA
- ✅ Performance optimization
- ✅ Security best practices

---

## 💼 Interview Talking Points

"I built Gym Bro, a production fitness tracking app that I use daily. Here's what makes it impressive:

1. **Full-stack**: React PWA + FastAPI backend + PostgreSQL
2. **Deployment**: Hosted on Vercel (serverless); auto-deploys on GitHub push
3. **Authentication**: Google OAuth 2.0 with JWT tokens; multi-tenant secure
4. **AI integration**: Google Cloud Vision API auto-detects foods from photos
5. **Mobile-first**: Responsive PWA; works offline with service workers
6. **Portfolio-grade**: Proper error handling, testing, documentation

Technical highlights:
- Implemented JWT-based auth with secure token refresh
- Optimized image processing pipeline with fallback UX
- Built responsive mobile-first UI with Tailwind
- Deployed containerized app to serverless infrastructure
- Integrated third-party APIs (Google OAuth, Vision)
- Achieved >90 Lighthouse PWA score

What I learned:
- How OAuth 2.0 really works (industry standard auth)
- Serverless architecture tradeoffs (cold starts vs. cost)
- Mobile-first design (touch targets, responsive layout)
- API integration patterns (error handling, rate limits)
- Security best practices (token management, user isolation)"

---

## 🚀 Ready to Start?

## **This Week (Week 1)**

## Getting Started with Phase 2 (OAuth)

1. **Review OAuth documentation**: [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md)
2. **Set up Google Cloud project** and obtain OAuth credentials
3. **Implement backend auth router** for OAuth flow
4. **Build frontend login page** with Google Sign-In
5. **Test with multiple Google accounts** to verify data isolation

For questions or implementation details, see the detailed guides in the documentation.
