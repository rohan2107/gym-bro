# Gym Bro: 12-Week Development Roadmap
**Updated**: January 13, 2026  
**Goal**: Portfolio project with personal daily use, Google SSO, and AI meal photos  
**Total time to completion**: 12 weeks of focused work

---

## 📊 Project Overview

### Vision
Build a **production-ready fitness tracking app** that serves as both:
1. **Personal daily-use tool** (for you to track workouts, meals, weight)
2. **Portfolio project** (demonstrates full-stack development, cloud deployment, AI integration)

### Success Criteria
- ✅ You use it daily on your phone for at least 2 weeks
- ✅ Deployed to production (Vercel) with real domain
- ✅ Google SSO working (multi-user ready)
- ✅ AI meal photo logging functional
- ✅ Portfolio-worthy code and documentation

### Tech Stack (Locked In)
- **Frontend**: React 18 + Vite + TypeScript + Tailwind (PWA)
- **Backend**: FastAPI + SQLModel + Pydantic v2
- **Database**: PostgreSQL (Neon)
- **Auth**: Google OAuth 2.0 + JWT
- **Hosting**: Vercel (free tier)
- **Storage**: Vercel Blob (photos)
- **AI**: Google Cloud Vision API

---

## 📅 12-Week Sprint Plan

### **Phase 1A: Mobile UX & Polish (Weeks 1–3)**
**Focus**: Make it usable on YOUR phone daily  
**You're the QA tester → catch all UX issues early**

**Deliverables**:
- [x] Bottom navigation (tab-based UI) ✅ **PR #1 - Jan 12, 2026**
- [x] Responsive mobile layout (full-width, single-column on phone) ✅ **Complete**
- [x] Edit/Delete functionality for meals & workouts ✅ **PR #3 - Jan 13, 2026**
- [x] Date picker for check-in history ✅ **PR #3 - Jan 13, 2026**
- [x] Offline caching (service worker) ✅ **PR #4 - Jan 13, 2026**
- [ ] Tested on actual iPhone + Android

**Key files to modify**:
- `gymbro-web/src/App.tsx` — Add tab state, bottom nav
- `gymbro-web/src/App.tsx` — Responsive CSS (mobile-first)
- `gymbro-web/src/components/` — New HistoryCard, updated Forms

**Definition of Done**:
- You can log check-in, meal, workout in <10 seconds from home screen
- Works offline (logs queue, sync when online)
- Lighthouse PWA score >90
- Works on iPhone and Android

**Documentation**:
- See `MOBILE_UI_SPEC.md` for detailed design

**Time estimate**: 2–3 weeks (you're building this one!)

---

### **Phase 1B: Vercel Deployment (Weeks 2–3, Parallel)**
**Focus**: Get production infrastructure ready**

**Deliverables**:
- [ ] Neon PostgreSQL database created
- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to Vercel Functions
- [ ] Photo storage (Vercel Blob) configured
- [ ] CORS properly configured
- [ ] Database backups automated

**Key infrastructure decisions made**:
- ✅ Database: Neon PostgreSQL (free tier, 3 GB)
- ✅ Backend: Vercel Functions (free tier, 100k invocations/month)
- ✅ Frontend: Vercel Static (free tier, unlimited)
- ✅ Photo storage: Vercel Blob (free tier, 1 GB, 1000 requests/month)
- ✅ CI/CD: GitHub → Vercel (auto-deploy on push)

**Definition of Done**:
- App is live at `https://yourusername.vercel.app`
- Backend API accessible at `https://gym-bro-api.vercel.app/health`
- Data persists in PostgreSQL (Neon)
- Can log data from production app

**Documentation**:
- See `DEPLOYMENT_GUIDE.md` for step-by-step setup

**Time estimate**: 1–2 weeks (mostly setup, some code changes for serverless)

**Cost**: $0 (all free tier)

---

### **Phase 2: Google OAuth Authentication (Weeks 4–6)**
**Focus**: Real multi-user authentication**

**Current state**: Header-based (X-User-Id) development mode  
**New state**: Google SSO + JWT tokens

**Deliverables**:
- [ ] Google Cloud project created
- [ ] OAuth 2.0 credentials generated
- [ ] Backend: Auth router with `/auth/google/callback` endpoint
- [ ] Backend: JWT token generation & verification
- [ ] Frontend: Login page with "Sign in with Google" button
- [ ] Frontend: Auth context + protected routes
- [ ] User data isolation verified (security testing)

**Backend changes**:
- New `app/routers/auth.py` — OAuth flow
- Update `app/models.py` — User model with email, display_name
- Update `app/deps.py` — JWT extraction instead of header
- Update all endpoints to check JWT token

**Frontend changes**:
- New `contexts/AuthContext.tsx` — Auth state management
- New `pages/Login.tsx` — Login page
- Update `App.tsx` → Redirect to login if not authenticated
- Update API client → Add JWT to Authorization header

**Testing**:
- [ ] Sign in with Google (personal email)
- [ ] Create check-in, meals, workouts
- [ ] Sign out → Data is secure
- [ ] Sign in as different user → Data is isolated
- [ ] Token refresh works (7-day expiry)

**Definition of Done**:
- You can sign in with Google
- Friends can sign in (separate user accounts)
- Each user's data is isolated (privacy verified)
- Production deployment works with OAuth

**Documentation**:
- See `GOOGLE_OAUTH_SETUP.md` for step-by-step OAuth setup (you'll learn Google Cloud!)

**Time estimate**: 2–3 weeks (OAuth is complex but well-documented)

**New skills**:
- ✅ Google Cloud Console navigation
- ✅ OAuth 2.0 protocol understanding
- ✅ JWT token management
- ✅ User isolation in multi-tenant apps

---

### **Phase 3A: Foundation Stabilization (Weeks 7–8)**
**Before we add AI, let's ensure everything is solid**

**Deliverables**:
- [ ] All endpoints have proper error handling + validation
- [ ] Frontend unit tests (Vitest + React Testing Library)
- [ ] E2E tests for happy path (Playwright)
- [ ] Backend test coverage expanded to 85%+
- [ ] CORS verified for both localhost + production
- [ ] Data migration strategy (if schema changes)
- [ ] Performance optimized (response time <200ms)
- [ ] Monitoring set up (error tracking, logs)

**Definition of Done**:
- App is stable for daily use
- No crashes or data loss
- Can deploy new code without issues
- Ready for AI integration

**Time estimate**: 1–2 weeks

---

### **Phase 3B: AI Meal Photo Pipeline (Weeks 9–12)**
**Focus**: Differentiated feature — auto-log meals from photos**

**Architecture**:
```
User taps "📷 Add from photo"
    ↓
Camera opens → captures meal photo
    ↓
Photo uploaded to Vercel Blob
    ↓
Backend calls Google Cloud Vision API
    ↓
Vision returns: [food items, portions, estimated calories]
    ↓
Backend enriches with USDA FoodData
    ↓
Frontend shows predictions: "Chicken breast, 150g, 240 cal, 35g protein"
    ↓
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

## 🎯 Success Milestones

| Week | Milestone | Status | Notes |
|------|-----------|--------|-------|
| 1–3 | Mobile UX done, using app daily | ⏳ | You're the first user |
| 2–3 | Deployed to Vercel | ⏳ | Live on internet |
| 4–6 | Google SSO working | ⏳ | Friends can log in |
| 7–8 | Stable + tested | ⏳ | Ready for AI |
| 9–12 | AI meal photos | ⏳ | Differentiated feature |
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

1. **Review documentation**:
   - `MOBILE_UI_SPEC.md` — Design specs
   - `DEPLOYMENT_GUIDE.md` — Will do later
   - `GOOGLE_OAUTH_SETUP.md` — Will do later

2. **Start mobile UI**:
   - Add bottom navigation component
   - Make layout responsive (mobile-first)
   - Test on your phone

3. **Ask me any questions**:
   - Design questions? Ask about mobile UX
   - Implementation questions? Ask about React patterns
   - Architecture questions? Ask about tradeoffs

**Next meeting**: End of Week 1 review (demo mobile UI on your phone)

Let's build something impressive! 💪🚀
