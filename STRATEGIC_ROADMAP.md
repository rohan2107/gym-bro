# Gym Bro — Strategic Roadmap

**Last Updated**: January 12, 2026 (Post-MVP Commit)

---

## Current State Assessment

### ✅ What We Have (MVP Complete)
1. **Functional Backend**: FastAPI + SQLModel with CRUD for check-ins, meals, workouts, exercises, weight entries.
2. **Interactive Frontend**: React + Vite + TypeScript UI with three main logging flows, form validation, error handling.
3. **Developer Experience**: PowerShell start scripts, proper env configuration, passing tests.
4. **Foundation for Scale**: PostgreSQL-ready backend, monorepo structure, CI/CD placeholder.

### 🎯 Strategic Goals (12-Month Vision)
- **Phase 1 (Now—Feb)**: Solidify core logging, launch feature parity, harden UX.
- **Phase 2 (Mar—May)**: Authentication + multi-user, basic analytics dashboard.
- **Phase 3 (Jun—Aug)**: AI meal photo pipeline, advanced reporting.
- **Phase 4 (Sep—Dec)**: Mobile optimization, offline sync, community features.

---

## Proposed Roadmap (Prioritized)

### 🔴 **Phase 1: MVP Hardening & Feature Completion (Weeks 1–8)**

#### 1.1 UX Improvements & Completeness
- [ ] **Edit/Delete functionality**: Allow users to modify/remove logged meals and workouts
  - Endpoints: `PUT /food-logs/{id}`, `DELETE /food-logs/{id}`, `PUT /workouts/{id}`, `DELETE /workouts/{id}`
  - UI: Inline edit buttons or modal dialogs with confirmation
  - Priority: **HIGH** — Core workflow gap
  
- [ ] **Exercise Set CRUD in UI**: Currently API exists but UI doesn't expose it
  - Add form to workout logging: "Add exercise to this workout"
  - Show exercise list under workout details
  - Priority: **MEDIUM** — Nice-to-have for detailed tracking
  
- [ ] **Date navigation for check-ins**: Only shows today; allow viewing/editing past days
  - Add date picker or prev/next buttons
  - Load historical data on date change
  - Priority: **HIGH** — Retroactive logging is common
  
- [ ] **Loading states & skeletons**: Replace "Loading…" text with proper spinners/skeletons
  - Priority: **LOW** — Current UX is acceptable but polish needed

#### 1.2 Backend Robustness
- [ ] **Input validation hardening**:
  - Date format validation in `PUT /daily-checkins/{date}`
  - Numeric bounds (e.g., weight > 0, steps ≥ 0)
  - Max string lengths to prevent DB bloat
  - Priority: **HIGH** — Security & data integrity
  
- [ ] **Error messages**: Return structured error responses with validation details
  - Priority: **MEDIUM** — Better DX
  
- [ ] **CORS configuration**: Ensure backend accepts requests from frontend origins (dev + production)
  - Priority: **HIGH** — Required for any deployment
  
- [ ] **Database indexes review**: Ensure queries are optimized
  - Add composite index on `(user_id, checkin_date)` if not auto-indexed
  - Priority: **LOW** — Premature optimization; can monitor performance

#### 1.3 Frontend Polish
- [ ] **Form UX enhancements**:
  - Numeric inputs: show min/max hints
  - Text inputs: character count for longer fields (notes)
  - Confirm dialogs for destructive actions
  - Priority: **MEDIUM**
  
- [ ] **Mobile responsiveness**: Test on phones; adjust grid layout if needed
  - Current: `grid-cols-1 md:grid-cols-3` — may not work well on tablets
  - Priority: **MEDIUM** — Mobile-first is PWA goal
  
- [ ] **Service worker enhancements**: Proper offline support
  - Cache GET endpoints on successful fetch
  - Queue POST/PUT requests for when connection returns
  - Priority: **MEDIUM** — PWA core feature

#### 1.4 Testing & Quality
- [ ] **Backend test expansion**: Cover edge cases
  - Negative numbers, boundary values, malformed dates
  - User isolation (confirm user 2 can't see user 1's data)
  - Priority: **HIGH**
  
- [ ] **E2E tests**: Playwright or Cypress for happy path
  - Log check-in → log meal → log workout → refresh → verify persistence
  - Priority: **MEDIUM** — Prevents regression
  
- [ ] **Type coverage**: Run `tsc --noEmit` in CI
  - Priority: **LOW** — Already strict, but automation helps

---

### 🟡 **Phase 2: Authentication & Multi-User (Weeks 9–16)**

#### 2.1 Authentication System
- [ ] **Choose auth strategy**: JWT, OAuth (Google/Apple), or session-based?
  - **Decision needed**: What's your preference? OAuth is simplest for MVP (no password management), JWT is more flexible.
  - Priority: **CRITICAL**
  
- [ ] **Implement auth flow**:
  - Backend: Auth router with login/register/logout/refresh endpoints
  - Frontend: Auth context, login page, redirect on 401
  - Storage: HttpOnly cookies (JWT) or localStorage (if JWT + CSRF protection)
  - Priority: **CRITICAL**
  
- [ ] **User profile model**: Store auth info, display name, email, preferences
  - Priority: **HIGH**

#### 2.2 Multi-User Infrastructure
- [ ] **Replace X-User-Id header with JWT claim**: Extract user_id from token instead of header
  - Priority: **HIGH**
  
- [ ] **User isolation verification**: Ensure all queries filter by authenticated user
  - Priority: **CRITICAL** — Security issue if missed
  
- [ ] **Session management**: Logout, token refresh, "remember me"
  - Priority: **MEDIUM**

#### 2.3 Sharing & Permissions (Future)
- [ ] **Share reports with friends**: Allow read-only access to trends/summaries
  - Priority: **LOW** — Post-launch feature

---

### 🟠 **Phase 3: Analytics & Insights (Weeks 17–24)**

#### 3.1 Dashboard MVP
- [ ] **Create `gymbro-analytics/` module**: Python data processing library
  - Functions: `calculate_weekly_avg_weight()`, `meal_calories_summary()`, `workout_frequency()`, etc.
  - Priority: **HIGH**
  
- [ ] **Analytics endpoints** (new router: `analytics.py`):
  - `GET /analytics/weight-trend?days=30` → list of (date, weight, 7-day avg)
  - `GET /analytics/calories-summary?week=2026-W02` → daily totals, avg
  - `GET /analytics/workout-stats?days=30` → count, frequency
  - Priority: **HIGH**
  
- [ ] **Frontend dashboard page**:
  - Line chart: weight trend (Chart.js or Recharts)
  - Bar chart: weekly calorie intake
  - Cards: streak counter (consecutive workout days), avg weight, etc.
  - Priority: **HIGH**

#### 3.2 Goal Tracking
- [ ] **Goals model**: User can set targets (target weight, daily protein, workouts/week)
  - Priority: **MEDIUM**
  
- [ ] **Goal progress display**: Show % toward target, countdown
  - Priority: **MEDIUM**
  
- [ ] **Notifications**: Alert when goal is met or missed (future)
  - Priority: **LOW**

---

### 🔵 **Phase 4: AI & Automation (Weeks 25–36)**

#### 4.1 Meal Photo Logging
- [ ] **Photo upload endpoint**: `POST /food-logs/from-photo` + multipart file
  - Store in cloud storage (AWS S3, Google Cloud Storage, or local)
  - Return presigned URL for frontend display
  - Priority: **HIGH** — Core vision feature
  
- [ ] **AI inference pipeline**:
  - Integrate vision API (OpenAI Vision, Google Cloud Vision, or Clarifai)
  - Extract: food items, estimated portion sizes, calories, macros
  - Return structured response to frontend
  - Priority: **HIGH**
  
- [ ] **Frontend photo capture**:
  - Camera input in PWA
  - Display AI predictions with ability to adjust/confirm
  - Create FoodLog with AI-suggested values
  - Priority: **HIGH**

#### 4.2 Smart Recommendations (Optional, Phase 4B)
- [ ] **Pattern analysis**: Detect eating habits, suggest hydration, spot trends
  - Priority: **MEDIUM**
  
- [ ] **Meal suggestions**: Recommend recipes based on goals + history
  - Priority: **LOW** — Nice-to-have

---

### 🟢 **Phase 5: Deployment & Operations (Ongoing)**

#### 5.1 Containerization
- [ ] **Docker**:
  - Dockerfile for backend (Python 3.11 + FastAPI)
  - Dockerfile for frontend (Node builder + static server)
  - docker-compose.yml for local dev + production services
  - Priority: **MEDIUM** — Improves portability
  
- [ ] **GitHub Actions CI/CD**:
  - Run tests on push
  - Build Docker images on release
  - Deploy to cloud (AWS, Heroku, DigitalOcean, or self-hosted)
  - Priority: **HIGH** — Required for any production deployment

#### 5.2 Database & Monitoring
- [ ] **PostgreSQL migration**: Validate schema works on Postgres
  - Priority: **HIGH** — Required before production
  
- [ ] **Backups & recovery**: Automated daily backups, restore procedure
  - Priority: **MEDIUM**
  
- [ ] **Logging & monitoring**: Error tracking (Sentry), performance monitoring (New Relic or similar)
  - Priority: **MEDIUM** — Aids debugging in production

#### 5.3 Infrastructure Decisions
- [ ] **Hosting choice**: Where will this run? (AWS, Heroku, DigitalOcean, VPS, self-hosted?)
  - **Decision needed**: Cost vs. complexity tradeoff?
  - Priority: **CRITICAL**
  
- [ ] **CDN for static assets**: Serve frontend from CDN (Cloudflare, AWS CloudFront)
  - Priority: **MEDIUM** — Speeds up first load

---

## Key Decisions Needed (From You)

### 1. **Authentication Strategy** (Phase 2)
   - **Option A**: OAuth (Google/Apple/GitHub)
     - Pros: No password management, familiar UX, fast to implement
     - Cons: Depends on third-party, privacy concerns for some users
   
   - **Option B**: JWT + self-managed auth
     - Pros: Full control, privacy-first, works offline-first
     - Cons: Password management overhead, CSRF protection needed
   
   - **Option C**: Session-based (cookies)
     - Pros: Simple, battle-tested
     - Cons: Less flexible for mobile/PWA
   
   **Recommendation**: OAuth (Option A) for fastest MVP; Phase 2B can add self-auth.

### 2. **AI Vision Provider** (Phase 4)
   - **Option A**: OpenAI Vision API
     - Pros: State-of-the-art accuracy, good UX
     - Cons: Costs $0.01/image, requires API key management
   
   - **Option B**: Google Cloud Vision
     - Pros: Good accuracy, generous free tier
     - Cons: Setup complexity, GCP account management
   
   - **Option C**: Clarifai (food-specific model)
     - Pros: Food-focused, decent accuracy
     - Cons: Smaller community, less documentation
   
   - **Option D**: On-device TensorFlow Lite model
     - Pros: Privacy, offline, free
     - Cons: Lower accuracy, limited to pre-trained model
   
   **Recommendation**: Option B (Google Cloud Vision) for balance of cost/accuracy/ease.

### 3. **Hosting & Deployment** (Phase 5)
   - **Option A**: Heroku (traditional, easiest)
     - Cost: ~$50/month (free tier deprecated)
     - Pros: Works out-of-box, Postgres included
     - Cons: Limited customization, vendor lock-in
   
   - **Option B**: DigitalOcean (VPS + app platform)
     - Cost: ~$12/month (VPS) + ~$15/month (managed DB)
     - Pros: Simple, affordable, good docs
     - Cons: More manual ops
   
   - **Option C**: AWS (Lambda + RDS)
     - Cost: ~$10–30/month (highly variable)
     - Pros: Scalable, feature-rich, free tier available
     - Cons: Steep learning curve, complex
   
   - **Option D**: Self-hosted (VPS + local Docker)
     - Cost: ~$5–10/month
     - Pros: Full control, cheapest
     - Cons: You manage backups, security, uptime
   
   **Recommendation**: DigitalOcean (Option B) — sweet spot of simplicity, cost, and control.

### 4. **Photo Storage** (Phase 4)
   - **Option A**: AWS S3
     - Cost: $0.023/GB stored
     - Pros: Industry standard, reliable
     - Cons: AWS complexity
   
   - **Option B**: Google Cloud Storage
     - Cost: $0.020/GB stored
     - Pros: Easy integration with Vision API
     - Cons: Google lock-in
   
   - **Option C**: MinIO (self-hosted S3-compatible)
     - Cost: Storage only (on your VPS)
     - Pros: Cheap, private, portable
     - Cons: You manage it
   
   - **Option D**: Local storage on VPS + backup to S3
     - Cost: ~$5/month
     - Pros: Fast serving, cheap
     - Cons: Backup complexity
   
   **Recommendation**: Option B (Google Cloud Storage) — integrates well with Vision API.

### 5. **First Paid Feature** (Post-MVP)
   - What would you charge for? (e.g., AI photo logging, export reports, premium analytics)
   - Or keep it free and monetize via ads/sponsorships?
   - **Decision needed**: Business model.

---

## Implementation Priorities (TL;DR)

### Next 4 Weeks (Weeks 1–4)
1. **Edit/Delete for meals & workouts** (HIGH impact, quick ROI)
2. **Date navigation for check-ins** (HIGH impact)
3. **Input validation hardening** (HIGH impact, security)
4. **CORS configuration** (HIGH impact, deployment blocker)

### Weeks 5–8
1. **E2E tests** (prevents regression, aids refactoring)
2. **Mobile responsiveness** (PWA goal)
3. **Form UX enhancements** (polish)

### Weeks 9–16 (Phase 2)
1. **OAuth integration** (auth blocker)
2. **Multi-user verification** (security)

### Weeks 17+
1. **Analytics dashboard** (Phase 3)
2. **AI photo pipeline** (Phase 4)

---

## Success Metrics
- **Engagement**: Average logs/day, DAU, retention after 1 month
- **Quality**: Test coverage (>80%), Lighthouse score (>90), error rate (<1%)
- **Performance**: Page load <2s, API response <200ms
- **Adoption**: Users for 1 week+, feature usage distribution

---

## Notes
- **Current tech stack is solid**: No major overhauls needed; build incrementally.
- **MVP scope was good**: Picked the right 3 features; avoid scope creep.
- **Start with quick wins**: Edit/Delete and date navigation are 2–3 day tasks with big UX impact.
- **Defer infrastructure**: Don't deploy to production yet; consolidate core features first.
