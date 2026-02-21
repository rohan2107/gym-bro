# Architecture

**Last Updated**: February 21, 2026  
**Status**: Production (Phase 3 Complete — Testing & CI/CD)
**Phase**: Phases 1-3 Complete, Phase 4 (AI Photo Logging) Next

---

## Tech Stack

**Frontend**:
- React 18, TypeScript, Vite
- Tailwind CSS for styling
- PWA with service worker (offline support)
- Bottom navigation for mobile-first UX

**Backend**:
- FastAPI (async Python web framework)
- SQLModel + Pydantic v2 (type-safe ORM)
- PostgreSQL on Neon (serverless)
- Google OAuth 2.0 + JWT (httpOnly cookies)

**Hosting**:
- Vercel (frontend + serverless functions)
- Neon PostgreSQL (managed database)
- Free tier supports MVP usage

**Testing & CI/CD**:
- pytest (backend: 47 tests, 85% coverage)
- Vitest + React Testing Library (frontend: 34 tests, 80% coverage)
- GitHub Actions (automated quality gates)
- Alembic (database migrations)

---

## System Architecture

```
┌──────────────────┐
│  User (Browser)  │
└────────┬─────────┘
         │
         ↓
┌────────────────────────────────────────┐
│  Frontend (Vercel)                     │
│  React + TypeScript + Tailwind         │
│                                        │
│  Pages:                                │
│  - Today: Daily check-ins              │
│  - Meals: Food logging                 │
│  - Workout: Exercise tracking          │
│  - Profile: User settings              │
│                                        │
│  Auth: AuthContext + OAuth flow        │
└────────┬───────────────────────────────┘
         │ HTTPS
         ↓
┌────────────────────────────────────────┐
│  Backend (Vercel Functions)            │
│  FastAPI + SQLModel                    │
│                                        │
│  Routers:                              │
│  - /auth/* (OAuth + JWT)               │
│  - /daily-checkins (upsert by date)    │
│  - /food-logs (full CRUD)              │
│  - /workouts (full CRUD)               │
│  - /weight-entries (full CRUD)         │
│  - /exercise-sets (full CRUD)          │
│  - /health (monitoring)                │
│                                        │
│  Auth: JWT from httpOnly cookie        │
│  User Isolation: All queries filtered  │
└────────┬───────────────────────────────┘
         │
         ↓
┌────────────────────────────────────────┐
│  PostgreSQL (Neon)                     │
│  - Serverless managed database          │
│  - Automatic SSL + backups              │
│                                        │
│  Tables:                                │
│  - users (google_id, email, name)       │
│  - daily_checkins (weight, steps, etc)  │
│  - food_logs (description, macros)      │
│  - workouts (name, notes)               │
│  - exercise_sets (workout FK, reps)     │
│  - weight_entries (value, date)         │
└─────────────────────────────────────────┘
```

---

## Data Model

**User**:
```python
- id: int (primary key)
- google_id: str (OAuth unique ID)
- email: str
- display_name: str  
- picture_url: str
- created_at: datetime
```

**DailyCheckIn** (one per user per date):
```python
- id: int
- user_id: int (FK → users)
- date: date (unique per user)
- weight: float | None
- steps: int | None
- trained_today: bool
- protein_target: int | None
- notes: str | None
```

**FoodLog**:
```python
- id: int
- user_id: int (FK → users)
- description: str
- calories: int | None
- protein_g: float | None
- carbs_g: float | None
- fat_g: float | None
- timestamp: datetime
```

**Workout**:
```python
- id: int
- user_id: int (FK → users)
- name: str
- notes: str | None
- created_at: datetime
```

**ExerciseSet** (child of Workout):
```python
- id: int
- workout_id: int (FK → workouts)
- exercise_name: str
- reps: int | None
- weight_kg: float | None
```

**WeightEntry**:
```python
- id: int
- user_id: int (FK → users)
- value: float
- date: date
- notes: str | None
```

---

## Authentication Flow

1. User clicks "Sign in with Google"
2. Frontend redirects to `/api/auth/google/login`
3. Backend generates OAuth URL → redirects to Google
4. Google authenticates → redirects back with code
5. Backend exchanges code for user info (email, name, picture)
6. Backend creates/updates user record
7. Backend generates JWT token (HS256, 7-day expiry)
8. Backend sets httpOnly cookie with JWT
9. Frontend receives auth status, loads app

**JWT Validation**:
- All protected routes validate JWT from cookie
- `get_user_id()` dependency extracts user_id from token
- Invalid/expired tokens → 401 Unauthorized

**User Isolation**:
- All database queries filter by `user_id`
- Users can only see/modify their own data
- Enforced at dependency injection layer

---

## API Endpoints

**Auth**:
- `GET /api/auth/google/login` — Initiate OAuth flow
- `GET /api/auth/google/callback` — Handle OAuth response
- `GET /api/auth/me` — Get current user info
- `POST /api/auth/logout` — Clear JWT cookie

**Check-ins**:
- `GET /api/daily-checkins` — List all check-ins
- `GET /api/daily-checkins/today` — Get today's check-in
- `GET /api/daily-checkins/{date}` — Get by specific date
- `PUT /api/daily-checkins/{date}` — Upsert for date

**Food Logs**:
- `GET /api/food-logs` — List all for user
- `GET /api/food-logs/{id}` — Get single log
- `POST /api/food-logs` — Create new
- `PUT /api/food-logs/{id}` — Update
- `DELETE /api/food-logs/{id}` — Delete

**Workouts**:
- `GET /api/workouts` — List all for user
- `GET /api/workouts/{id}` — Get single workout
- `POST /api/workouts` — Create new
- `PUT /api/workouts/{id}` — Update
- `DELETE /api/workouts/{id}` — Delete

**Weight Entries**:
- `GET /api/weight-entries?from={date}&to={date}` — List all for user (optional date range)
- `POST /api/weight-entries` — Create new
- `PUT /api/weight-entries/{id}` — Update entry
- `DELETE /api/weight-entries/{id}` — Delete

**Exercise Sets**:
- `GET /api/exercise-sets?workout_id={id}` — List for workout
- `POST /api/exercise-sets` — Create new
- `PUT /api/exercise-sets/{id}` — Update set
- `DELETE /api/exercise-sets/{id}` — Delete

**Health**:
- `GET /api/health` — Service health check

---

## API Versioning

**Current Status**: All endpoints are unversioned (v1 implicit).

**Strategy**:
- Breaking changes will introduce `/v2/` prefix
- Current endpoints remain stable for backward compatibility
- Deprecated endpoints marked in docs 6 months before removal
- OpenAPI spec available at `/docs` (FastAPI auto-generated)

**Planned Changes**:
- Phase 4 will add `/api/food-logs/from-photo` (non-breaking addition)
- Phase 5 will add `/api/analytics/*` endpoints (new resource)

---

## Security

**Authentication**:
- Google OAuth 2.0 (industry standard)
- JWT tokens in httpOnly cookies (XSS protection)
- 7-day token expiry with auto-refresh

**Authorization**:
- All endpoints require valid JWT
- User isolation enforced at query level
- No cross-user data access possible

**Database**:
- Parameterized queries (SQLAlchemy ORM)
- Automatic SSL (Neon managed PostgreSQL)
- Foreign key constraints enforced

**API**:
- CORS configured for production domain
- Input validation with Pydantic
- Automatic request/response validation

---

## Performance

**Current Metrics**:
- Page load: ~1-2s (Vite + Vercel CDN)
- API response: <200ms (async FastAPI)
- Cold start: 1-3s (acceptable for MVP)
- PWA score: >90 (offline support + caching)

**Optimizations**:
- Service worker caches API responses
- Lazy-loaded routes (React.lazy)
- Database indexes on user_id + date
- Connection pooling enabled

---

## Testing

**Backend** (pytest):
- 47 tests, 85% coverage
- Router tests (all CRUD endpoints)
- Auth utility tests (JWT validation)
- Dependency tests (user isolation)
- Integration tests with test database

**Frontend** (Vitest + React Testing Library):
- 34 tests, 80% coverage
- Component tests (BottomNav, OfflineIndicator)
- Utility tests (date formatting, error handling)
- Integration tests (API client)

## Known Limitations

**Cold Starts**: Vercel serverless functions have ~1-2s cold start latency on first request after idle period (mitigated by Vercel's edge network for subsequent requests).

**Error Recovery**: No automatic retry logic for failed API requests; users must manually retry operations (planned for Phase 4).

**Offline Editing**: Weight entries and food logs cannot be edited in offline mode; only creation is supported via IndexedDB queue.

**Profile Page**: Currently displays placeholder data; full settings and user preferences coming in Phase 5.

**Rate Limiting**: No per-user rate limiting implemented; relies on Vercel's platform-level DDoS protection (as of February 2026).

**CI/CD** (GitHub Actions):
- Automated test runs on PR
- Parallel jobs (backend + frontend)
- Type checking, linting, build verification
- All checks must pass before merge

---

## Deployment

**Production Setup**:
```bash
# Frontend + Backend deployed to Vercel
git push origin main → auto-deploys

# Database migrations (Alembic)
cd gymbro-api
alembic upgrade head
```

**Environment Variables**:
```
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://...
```

**Monitoring**:
- Vercel logs (application)
- Neon metrics (database)
- GitHub Actions (CI/CD status)

**Rollback Procedures**:
```bash
# Rollback frontend/backend deployment (Vercel)
# Via Vercel Dashboard: Select previous deployment → "Promote to Production"
# Or via CLI:
vercel rollback <deployment-url>

# Rollback database migration (Alembic)
cd gymbro-api
alembic downgrade -1  # Rollback one migration
# Or: alembic downgrade <revision>
```

**Troubleshooting**:
- **Cold Start Issues**: Check Vercel logs for function timeouts
- **Database Connection Errors**: Verify DATABASE_URL in Vercel env vars
- **Auth Failures**: Confirm GOOGLE_CLIENT_ID matches OAuth consent screen
- **Migration Conflicts**: Run `alembic heads` to check for multiple heads

---

## Future Enhancements

**Phase 4**: AI Meal Photo Logging
- Google Cloud Vision API
- Vercel Blob storage
- USDA FoodData nutrition lookup

**Phase 5**: Energy Balance Analytics
- TDEE calculator with adaptive algorithm
- Weight loss validation
- Energy balance dashboard

**Infrastructure**:
- E2E tests with Playwright
- Error tracking (Sentry)
- Performance monitoring (Vercel Analytics)

---

## Related Documentation

- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) — Development phases
- [Testing Guide](TESTING_GUIDE.md) — Test suite and commands
- [Phase 4 Implementation Plan](PHASE4_AI_MEAL_PLAN.md) — AI photo logging details


