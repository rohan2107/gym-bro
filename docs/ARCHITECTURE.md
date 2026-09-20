# Architecture

**Last Updated**: September 16, 2026
**Status**: Phase 0 of the [AI Roadmap](AI_ROADMAP.md) complete — AI photo logging implemented
end to end (backend + UI), pending a verification run against real API keys

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS |
| **Backend** | FastAPI (async), SQLModel, Pydantic v2 |
| **Database** | PostgreSQL on Neon (serverless) |
| **Auth** | Google OAuth 2.0 + JWT (httpOnly cookies) |
| **AI Services** | Google Cloud Vision REST API, USDA FoodData Central |
| **Hosting** | Vercel (frontend + serverless functions) |
| **CI/CD** | GitHub Actions (9 jobs, 8 required) |
| **Migrations** | Alembic |

---

## System Overview

```
┌──────────────────┐
│  User (Browser)  │
└────────┬─────────┘
         │ HTTPS
         ↓
┌────────────────────────────────────────┐
│  Frontend (Vercel)                     │
│  React + TypeScript + Tailwind         │
│                                        │
│  Pages:                                │
│  - Today: Daily check-ins              │
│  - Meals: Food logging + photo capture │
│  - Workout: Exercise tracking          │
│  - Profile: User settings              │
│                                        │
│  Auth: AuthContext + OAuth flow        │
│  PWA: Service worker + offline cache   │
└────────┬───────────────────────────────┘
         │
         ↓
┌────────────────────────────────────────┐
│  Backend (Vercel Serverless)           │
│  FastAPI + SQLModel                    │
│                                        │
│  Routers:                              │
│  - /auth/*           OAuth + JWT       │
│  - /daily-checkins   Upsert by date    │
│  - /food-logs        CRUD + photo AI   │
│  - /workouts         CRUD              │
│  - /weight-entries   CRUD              │
│  - /exercise-sets    CRUD              │
│  - /health           Monitoring        │
│                                        │
│  Services:                             │
│  - VisionService     Food detection    │
│  - NutritionService  USDA lookup       │
│  - RateLimiter       Per-user quotas   │
│                                        │
│  Auth: JWT cookie + Bearer token       │
│  User Isolation: All queries filtered  │
└────────┬───────────────────────────────┘
         │
    ┌────┴────┬──────────────┐
    ↓         ↓              ↓
┌──────────┐ ┌──────────┐ ┌──────────┐
│PostgreSQL│ │Vision API│ │USDA API  │
│ (Neon)   │ │ (Google) │ │  (USDA)  │
└──────────┘ └──────────┘ └──────────┘
```

---

## Data Model

```
User
├── id, email, google_id, display_name, picture_url
├── photo_count, last_photo_date          ← rate limiting
├── created_at
│
├── DailyCheckIn (one per user per date)
│   ├── checkin_date, weight, trained, steps, protein_met, notes
│   ├── → FoodLog[]
│   ├── → Workout[]
│   └── → WeightEntry[]
│
├── FoodLog
│   ├── description, calories, protein_g, carbs_g, fat_g
│   ├── logged_at
│   └── → NutrientEntry[] (AI-detected per-item breakdown)
│
├── Workout
│   ├── name, note, started_at
│   └── → ExerciseSet[]
│       └── exercise_name, reps, weight_kg, rpe
│
└── WeightEntry
    └── for_date, weight_kg, note
```

All models enforce user isolation via `user_id` foreign key. Queries are filtered at the dependency injection layer — no cross-user access is possible.

**Schema ownership**: Alembic is the single source of truth. Application startup only verifies
that the database is reachable (`check_db_connection()`); it does not create tables and does
not write. Migrations are applied by the `db-migrate` CI job on push to main, or manually with
`alembic upgrade head`.

---

## API Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auth/google/login` | Initiate OAuth flow |
| GET | `/api/auth/google/callback` | Handle OAuth response |
| GET | `/api/auth/me` | Current user info |
| POST | `/api/auth/logout` | Clear JWT cookie |

### Daily Check-ins
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/daily-checkins` | List all |
| GET | `/api/daily-checkins/today` | Today's check-in |
| GET | `/api/daily-checkins/{date}` | By specific date |
| PUT | `/api/daily-checkins/{date}` | Upsert for date |

### Food Logs
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/food-logs` | List all |
| POST | `/api/food-logs` | Create manually |
| POST | `/api/food-logs/from-photo` | **AI photo analysis** |
| GET | `/api/food-logs/{id}` | Get single |
| PUT | `/api/food-logs/{id}` | Update |
| DELETE | `/api/food-logs/{id}` | Delete |

### Workouts & Exercise Sets
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/workouts` | List all |
| POST | `/api/workouts` | Create |
| GET | `/api/workouts/{id}` | Get single |
| PUT | `/api/workouts/{id}` | Update |
| DELETE | `/api/workouts/{id}` | Delete |
| GET | `/api/exercise-sets?workout_id={id}` | List for workout |
| POST | `/api/exercise-sets` | Create |
| PUT | `/api/exercise-sets/{id}` | Update |
| DELETE | `/api/exercise-sets/{id}` | Delete |

### Weight Entries
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/weight-entries` | List (optional date range) |
| POST | `/api/weight-entries` | Create |
| PUT | `/api/weight-entries/{id}` | Update |
| DELETE | `/api/weight-entries/{id}` | Delete |

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Service health check |

---

## AI Photo Logging Pipeline

```
Photo captured (multipart/form-data, max 10MB)
  → Content-type validation (image/* only)
  → Local image validation (Pillow: format, dimensions, size)
  → Rate limit check (30/day/user, atomic with FOR UPDATE)
  → Google Cloud Vision images:annotate → LABEL_DETECTION + WEB_DETECTION
  → Generic labels dropped, deduplicated, ranked, top 3 kept
  → USDA FoodData Central API → nutrition per detected food
  → Return predictions for user review/edit
  → User confirms → saved via standard POST /food-logs
```

Quota is reserved *before* the expensive calls and refunded if detection or nutrition lookup
fails, so a failed request does not cost the user a photo.

**Services** (`app/services/`):
- **VisionService** — Google Cloud Vision via its REST API (`images:annotate`) using an API
  key and `httpx`, not the `google-cloud-vision` client library: the client library needs
  service-account credentials rather than the API key this app is deployed with, and it would
  ship gRPC and protobuf into a serverless function for one HTTP POST. Mock mode is used when
  no key is configured.
- **NutritionService** — USDA FoodData Central with batch search and 10s HTTP timeout
- **RateLimiter** — Atomic `try_increment()` using `SELECT FOR UPDATE` to prevent race conditions
- **FoodMapping** — 60+ label → USDA query mappings for common foods

All services use FastAPI dependency injection for testability.

**Confidence scores**: Vision label scores are probabilities in [0, 1] and are thresholded at
0.70. Web-entity scores are unbounded relevance values that routinely exceed 1.0; they are
thresholded at 0.60 on the raw value and clamped to 1.0 before being reported.

**Frontend** (`gymbro-web/src/components/`):
- **PhotoCapture** — file input with `capture="environment"`, which opens the native camera on
  iOS Safari and Android Chrome and the file picker on desktop. Client-side type and 10MB size
  checks mirror the backend so bad files fail instantly. Shows remaining daily quota.
- **MealReview** — every predicted value is editable before saving. USDA figures are per 100g,
  which is rarely the portion eaten, and the UI says so rather than implying the estimate is
  authoritative. Failures surface next to the photo control and leave manual entry available.

---

## Authentication

1. User clicks "Sign in with Google" → frontend redirects to `/api/auth/google/login`
2. Backend generates OAuth URL → redirects to Google
3. Google authenticates → redirects with authorization code
4. Backend exchanges code for user info → creates/updates user record
5. Backend generates JWT (HS256, 7-day expiry) → sets httpOnly cookie
6. All protected routes validate JWT from cookie or `Authorization: Bearer` header
7. `get_user_id()` dependency extracts `user_id` — all queries filter by it

---

## Security

- **Auth**: Google OAuth 2.0 + JWT in httpOnly cookies, `SameSite=Lax` (XSS protection)
- **Isolation**: All DB queries filtered by `user_id` at dependency level
- **Validation**: Pydantic input validation, content-type checks on uploads
- **Upload limits**: 10MB file size, streaming in 64KB chunks to prevent memory exhaustion
- **Rate limiting**: Atomic per-user quotas with row-level locking
- **CORS**: Explicit allow-list — localhost dev origins plus the configured production
  origin. Deliberately *not* `https://.*\.vercel\.app`, which would make every site deployed
  on vercel.app an allowed credentialed origin. `CORS_PREVIEW_ORIGIN_REGEX` allows additional
  origins but is unset by default, since on Vercel the frontend and API share an origin and
  CORS is never consulted.
- **Credentials in logs**: the Vision API key is sent as an `X-Goog-Api-Key` header rather
  than a query parameter, because httpx embeds the request URL in `HTTPStatusError` and the
  photo endpoint logs that exception with `exc_info=True`.
- **API protection**: 10s timeout on all external calls
- **Error handling**: Generic user-facing messages, detailed internal logging with `exc_info=True`

---

## Testing

**160 backend tests** (pytest, ~4s) | **46 frontend tests** (Vitest, ~1s) | **206 total**

Backend coverage: **85%** (auth.py OAuth callbacks largely uncovered — requires a real Google
OAuth flow)

| Area | Tests | Coverage |
|------|-------|----------|
| Rate limiter (atomic behavior) | 17 | 84% |
| Photo endpoint (integration) | 16 | 89% |
| Nutrition service | 12 | 96% |
| Vision service (incl. mocked Vision REST API) | 25 | 96% |
| Requirements parity (prod vs CI) | 6 | n/a |
| Migrations (fresh-DB build + model match) | 4 | n/a |
| Food log CRUD | 9 | 89% |
| Workout + exercise sets | 11 | 91% |
| Auth utilities + deps | 19 | 81–94% |
| Daily check-ins | 11 | 81% |
| Weight entries | 9 | 96% |
| DB + lifespan + main | 19 | 75–83% |

CI pipeline runs on every PR: backend tests, backend lint (ruff, pinned — see
`gymbro-api/ruff.toml`), frontend tests, frontend lint, TypeScript type-check, frontend build
verification, and Vercel config validation. On push to main it also applies Alembic migrations
(`db-migrate`). The `all-checks-passed` gate requires 8 jobs; the Vercel preview smoke test
runs on PRs but is not part of the gate.

---

## Deployment

```bash
git push origin main  # Auto-deploys to Vercel
```

**Database migrations**: `cd gymbro-api && alembic upgrade head`

**Environment variables** (Vercel):
```
DATABASE_URL, JWT_SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
FRONTEND_URL, GOOGLE_VISION_API_KEY, USDA_API_KEY,
CORS_ALLOWED_ORIGINS (optional), CORS_PREVIEW_ORIGIN_REGEX (optional)
```

All are declared on the `Settings` model in `app/config.py`.

**Dependencies**: `api/requirements.txt` is what Vercel installs for the serverless function;
`gymbro-api/requirements.txt` is that set plus test tooling. `tests/test_requirements_parity.py`
enforces that the shared pins stay identical — a drift between the two previously broke the
photo endpoint in production while CI stayed green.

---

## Known Limitations

- **Vision integration unverified against the live API**: implemented and unit-tested against a
  mocked `images:annotate` endpoint, but not yet exercised with a real `GOOGLE_VISION_API_KEY`.
  Real label vocabulary may need additions to `NON_FOOD_LABELS` and `FOOD_MAPPING`.
- **Blocking database calls in async handlers**: the app uses synchronous SQLModel sessions
  throughout, including inside `async def` endpoints, so database latency occupies the event
  loop. This predates the photo endpoint and affects every router; resolving it means moving
  the data layer to async SQLAlchemy, tracked as its own piece of work rather than done
  piecemeal.
- **Cold starts**: Vercel serverless functions have ~1-2s cold start on first request after idle
- **Streaming**: Long-running streamed responses are not viable through the Mangum-wrapped app
  on Vercel functions — a constraint the [AI Roadmap](AI_ROADMAP.md) has to resolve before
  LLM features ship
- **Offline editing**: Service worker provides read-only cache; no offline writes yet
- **Profile page**: Displays placeholder data
- **HEIC photos**: macOS Photos exports HEIC, which Pillow cannot decode without an extra
  native library. Both the frontend and backend reject it with a message explaining how to get
  a JPEG. iOS Safari normally converts to JPEG before upload, but this has not been confirmed
  on a device.
- **Portion sizes**: USDA nutrition is per 100g; the review UI surfaces this but does not
  estimate actual portion size from the photo
- **Lint scope**: `ruff.toml` selects ruff's historical default rules (E4, E7, E9, F). Widening
  it (`UP`, `I`, `DTZ`) is a worthwhile separate change — roughly 200 findings, all stylistic


