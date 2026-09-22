# Architecture

**Last updated**: September 20, 2026
**Status**: Phase 0 merged. Planned work is in the [roadmap](ROADMAP.md).

How the system is built today. Decisions and their reasoning are in [adr/](adr/), operations in
[DEPLOYMENT.md](DEPLOYMENT.md), and the deeper design of individual features in
[AUTHENTICATION.md](AUTHENTICATION.md) and [PHOTO_ANALYSIS.md](PHOTO_ANALYSIS.md).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS |
| **Backend** | FastAPI (async), SQLModel, Pydantic v2 |
| **Database** | PostgreSQL on Neon (serverless) |
| **Auth** | Google OAuth 2.0 + JWT (httpOnly cookies) |
| **AI Services** | Gemini API (food recognition; Cloud Vision optional), USDA FoodData Central |
| **Hosting** | Vercel: static frontend plus one Python function serving the ASGI app directly |
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
│  - FoodRecognizer    Gemini / Vision   │
│  - NutritionService  Local USDA table  │
│  - RateLimiter       Per-user quotas   │
│                                        │
│  Auth: JWT cookie + Bearer token       │
│  User Isolation: All queries filtered  │
└────────┬───────────────────────────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌──────────┐ ┌──────────┐
│PostgreSQL│ │Gemini API│
│(Neon; incl.│ (Google) │
│USDA data)│ └──────────┘
└──────────┘
```

USDA FoodData Central is a one-time data source (`scripts/build_usda_dataset.py`), not a
runtime dependency - the request path never calls it. See
[ADR-0010](adr/0010-usda-as-a-local-reference.md).

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

## Photo analysis

A meal photo is validated, checked against the user's daily quota, sent to a recognition
service, matched to USDA nutrition data, and returned as editable predictions. Nothing is
saved until the user confirms.

```
POST /api/food-logs/from-photo
  validate (type, size, format, HEIC) -> reserve quota -> recognise -> USDA lookup -> predictions
```

Quota is reserved before the expensive calls and refunded when they fail. On a deployment the
endpoint refuses rather than serve mock data. Full behaviour, failure modes and limits are in
[PHOTO_ANALYSIS.md](PHOTO_ANALYSIS.md); the choice of recognition provider is
[ADR-0005](adr/0005-food-recognition-providers.md).

Services (`app/services/`) are injected through FastAPI dependencies, so tests replace them
and no test calls a real service: the configured `FoodRecognizer` (`GeminiRecognizer` or
`VisionService`), `NutritionService`, `RateLimiter`, and the `food_mapping` table.

---

## Authentication

Google OAuth 2.0 (authorization code flow); the API issues its own JWT as an httpOnly,
`SameSite=Lax` cookie, and `get_user_id()` extracts the user for every request. Setup, the
flow, the session model and known gaps are in [AUTHENTICATION.md](AUTHENTICATION.md).

---

## Security

- **Auth**: Google OAuth 2.0 + JWT in httpOnly cookies, `SameSite=Lax` (XSS protection)
- **Isolation**: All DB queries filtered by `user_id` at dependency level
- **Dev auth header**: `X-User-Id` lets a caller act as any user and exists only for local
  development and tests. It is enabled only when `ENVIRONMENT` is explicitly `development` or
  `test` (the default is `production`), and never on Vercel, which sets `VERCEL=1` itself, so
  it cannot be re-enabled by a misconfiguration.
- **Validation**: Pydantic input validation, content-type checks on uploads
- **Upload limits**: 10MB file size, streaming in 64KB chunks to prevent memory exhaustion
- **Rate limiting**: Atomic per-user quotas with row-level locking
- **CORS**: Explicit allow-list — localhost dev origins plus the configured production
  origin. Deliberately *not* `https://.*\.vercel\.app`, which would make every site deployed
  on vercel.app an allowed credentialed origin. `CORS_PREVIEW_ORIGIN_REGEX` allows additional
  origins but is unset by default, since on Vercel the frontend and API share an origin and
  CORS is never consulted.
- **Credentials in logs**: the Gemini and Vision keys are sent as headers
  (`x-goog-api-key`, `X-Goog-Api-Key`) rather than query parameters, because httpx
  embeds the request URL in `HTTPStatusError` and in its own INFO log. Services log status
  codes, not exception text, and the `httpx` logger is raised to WARNING at startup. Nutrition
  lookup has no credential at all since M1.0 - it queries a local table
  ([F13](AUDIT_2026-09.md#f13-api-key-in-the-request-url),
  [F15](AUDIT_2026-09.md#f15-usda-key-in-the-request-url-and-in-production-logs)).
- **API protection**: 10s timeout on all external calls
- **Error handling**: Generic user-facing messages, detailed internal logging with `exc_info=True`

Known gaps (no OAuth `state`, no `email_verified` check, raw provider errors returned to the
client) are tracked as open findings in the [audit](AUDIT_2026-09.md#open-findings).

---

## Testing

Backend (pytest) and frontend (Vitest) are each gated at 80% coverage in CI. Test counts are
deliberately not recorded here: they change with every pull request and were wrong in several
places within days of being written. Run the suites for the current numbers. The OAuth callback
in `auth.py` is largely uncovered because it needs a real Google flow.

| Backend area | What is covered |
|---|---|
| Gemini provider | Responses recorded from the live API, model fallback, parsing and validation, portion estimates, credentials |
| Vision provider | Parsing, filtering, credentials |
| Nutrition service | Local-table search seeded with representative rows, ranking, portion scaling, a database-failure path |
| Photo endpoint | Every failure path, mock-mode refusal (recognition only - nutrition lookup has none), USDA grounding and the AI-estimate fallback |
| Image validation | Format, size, HEIC |
| Auth | JWT utilities, dependencies, the development header, provider selection |
| Rate limiter | Atomicity, refunds |
| Resource routers | Check-ins, weight, workouts and sets, food-log CRUD |
| Structure | App wiring, CORS, lifespan and logging setup, database connection check |
| Guards | Requirements parity, runtime versions, migrations (see below) |

| Frontend area | What is covered |
|---|---|
| Photo capture | Type, HEIC and size checks, quota display, the data-use notice |
| Image resizing | Dimensions, no upscaling, orientation, quality fallback, decode failure |
| API client | The request helper, every endpoint, the photo upload |
| Meal review | Form behaviour, the basis of the numbers, and rescaling every macro when the portion is edited |
| Service worker | `public/sw.js` run against a fake cache: network-first pages, offline and slow-network fallback, permanent hashed assets, lifecycle |
| Components and utilities | Bottom navigation, offline indicator, helpers |

Four groups of tests exist to stop a specific past defect recurring: `test_requirements_parity.py`
(production and CI installing different dependencies), `test_runtime_versions.py` (CI testing
other Python and Node versions than Vercel builds on), `test_migrations.py` (a schema no
migration could build), and the CORS and development-header tests in `test_main.py` and
`test_deps.py`. The CI gates are listed in [DEPLOYMENT.md](DEPLOYMENT.md#cicd).

---

## Deployment

Merging to `main` deploys to Vercel and runs Alembic migrations against production. The
environment variables, the release and rollback procedure, and post-deploy checks are in
[DEPLOYMENT.md](DEPLOYMENT.md). `api/requirements.txt` is what Vercel installs;
`gymbro-api/requirements.txt` is that set plus test tooling and the local dev server (uvicorn
and its extras, which production never imports), and a test enforces that the shared pins
match and that nothing else drifts in.

---

## Planned architecture

The roadmap adds a retrieval and agent layer beside the existing services rather than
replacing them. Model calls go through one client so they can be recorded, replayed, traced and
bounded.

```
Routers (existing)          Assistant / agent (planned)
       |                              |
       |                     +--------+---------+
       |                     |   Tool registry  |  user id injected from the session
       |                     +--------+---------+
       |                              |
       v                              v
  Services  <------------ Retrieval (pgvector, citations)
       |                              |
       |                     +--------+---------+
       |                     |   LLM client     |  record / replay / passthrough
       |                     |  timeouts, retry |  tracing, cost, caching
       |                     +--------+---------+
       v                              v
   Postgres                  Hosted models (free tiers that stop at their limit)
```

See the [roadmap](ROADMAP.md) for the sequence and [EVALUATION.md](EVALUATION.md) for how each
layer is measured.

---

## Known limitations

- **Photo analysis needs `GEMINI_API_KEY` set on Vercel.** Portions and macros are estimates
  whose accuracy is unmeasured, and the review screen says whether they came from USDA or from
  the model alone. The Vision provider has never run against the live API. See
  [PHOTO_ANALYSIS.md](PHOTO_ANALYSIS.md).
- **Blocking database calls in async handlers.** Sessions are synchronous throughout, so
  database latency occupies the event loop. It affects every router and is scheduled as
  [M3.0](ROADMAP.md#m30-async-data-layer).
- **Streaming is undecided.** An earlier version of these docs said the app was
  "Mangum-wrapped" and could not stream. It is not; the handler exposes the ASGI app directly.
  Whether streaming works is to be settled by experiment ([ADR-0006](adr/0006-streaming-on-vercel.md)).
- **Cold starts.** A Vercel function and a Neon compute that have scaled to zero each add
  latency to the first request.
- **Offline writes** are not supported; the service worker provides a read-only cache. The page
  is fetched network-first with the cached shell as fallback, and hashed assets are cached
  permanently.
- **Profile page** shows placeholder data.
- **Nutrition is per 100g**, and HEIC photos are rejected; see
  [PHOTO_ANALYSIS.md](PHOTO_ANALYSIS.md#limits).
- **Lint scope.** `ruff.toml` selects only the historical default rules; widening it is a
  separate change of roughly 200 stylistic findings.
