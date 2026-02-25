# Architecture

**Last Updated**: February 25, 2026
**Status**: Phase 4.2 Complete — AI Photo Logging Backend Ready

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS |
| **Backend** | FastAPI (async), SQLModel, Pydantic v2 |
| **Database** | PostgreSQL on Neon (serverless) |
| **Auth** | Google OAuth 2.0 + JWT (httpOnly cookies) |
| **AI Services** | Google Cloud Vision API, USDA FoodData Central |
| **Hosting** | Vercel (frontend + serverless functions) |
| **CI/CD** | GitHub Actions (7 parallel jobs) |
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
│  - Meals: Food logging + photo upload  │
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
Photo uploaded (multipart/form-data, max 10MB)
  → Content-type validation (image/* only)
  → Rate limit check (30/day/user, atomic with FOR UPDATE)
  → Google Cloud Vision API → food labels with confidence scores
  → USDA FoodData Central API → nutrition per detected food
  → Return predictions for user review/edit
  → User confirms → saved via standard POST /food-logs
```

**Services** (`app/services/`):
- **VisionService** — Google Cloud Vision integration with mock mode for development
- **NutritionService** — USDA FoodData Central with batch search and 10s HTTP timeout
- **RateLimiter** — Atomic `try_increment()` using `SELECT FOR UPDATE` to prevent race conditions
- **FoodMapping** — 60+ label → USDA query mappings for common foods

All services use FastAPI dependency injection for testability.

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

- **Auth**: Google OAuth 2.0 + JWT in httpOnly cookies (XSS protection)
- **Isolation**: All DB queries filtered by `user_id` at dependency level
- **Validation**: Pydantic input validation, content-type checks on uploads
- **Upload limits**: 10MB file size, streaming in 64KB chunks to prevent memory exhaustion
- **Rate limiting**: Atomic per-user quotas with row-level locking
- **API protection**: CORS configured for production domain, 10s timeout on all external calls
- **Error handling**: Generic user-facing messages, detailed internal logging with `exc_info=True`

---

## Testing

**133 backend tests** (pytest, ~4s) | **27 frontend tests** (Vitest, ~3s) | **160 total**

Backend coverage: **84%** (auth.py OAuth callbacks excluded — requires real Google OAuth flow)

| Area | Tests | Coverage |
|------|-------|----------|
| Rate limiter (atomic behavior) | 17 | 84% |
| Photo endpoint (integration) | 16 | 89% |
| Nutrition service | 12 | 96% |
| Vision service | 10 | 84% |
| Food log CRUD | 9 | 89% |
| Workout + exercise sets | 11 | 91% |
| Auth utilities + deps | 19 | 81–94% |
| Daily check-ins | 11 | 81% |
| Weight entries | 9 | 96% |
| DB + lifespan + main | 19 | 75–83% |

CI pipeline runs 7 parallel jobs on every PR: backend tests, backend lint, frontend tests, frontend lint, TypeScript type-check, frontend build verification, and Vercel config validation.

---

## Deployment

```bash
git push origin main  # Auto-deploys to Vercel
```

**Database migrations**: `cd gymbro-api && alembic upgrade head`

**Environment variables** (Vercel):
```
DATABASE_URL, JWT_SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
GOOGLE_REDIRECT_URI, GOOGLE_VISION_API_KEY, USDA_API_KEY
```

---

## Known Limitations

- **Cold starts**: Vercel serverless functions have ~1-2s cold start on first request after idle
- **Offline editing**: Service worker provides read-only cache; no offline writes yet
- **Profile page**: Displays placeholder data; full settings planned for Phase 5
- **Frontend for photo logging**: Backend ready, frontend UI (Phase 4.3) not yet built


