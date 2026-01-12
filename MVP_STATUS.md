# Gym Bro — MVP Completion Status

## ✅ Backend (FastAPI + SQLModel)
- [x] Core models: `User`, `DailyCheckIn`, `FoodLog`, `Workout`, `ExerciseSet`, `WeightEntry`, `NutrientEntry`.
- [x] Routers: `daily_checkins`, `food_logs`, `workouts`, `weight_entries`, `exercise_sets`, `health`.
- [x] Endpoints:
  - `GET /daily-checkins/today` — Fetch today's check-in.
  - `PUT /daily-checkins/{date}` — Upsert check-in (weight, trained, protein_met, steps, notes).
  - `GET /food-logs/` — List food logs for user.
  - `POST /food-logs/` — Create food log (description, optional calories/macros).
  - `GET /workouts` — List workouts for user (ordered newest first).
  - `POST /workouts` — Create workout (name, optional note).
  - `GET /health` — Health check.
- [x] User scoping via `X-User-Id` header.
- [x] SQLite dev DB; Postgres-ready via `.env`.
- [x] Tests pass: check-in CRUD, food log CRUD, workout CRUD.
- [x] DB init on startup (SQLModel auto-create all tables).

## ✅ Frontend (React + Vite + TypeScript + Tailwind)
- [x] App.tsx: Interactive UI with state management.
  - Daily check-in card: view/update weight, steps, trained/protein flags, notes.
  - Meals column: log description + optional calories; list newest first.
  - Workouts column: log name + optional note; list newest first.
- [x] API client (src/lib/api.ts): typed requests with `X-User-Id` header.
- [x] Form components (src/components/Forms.tsx): CheckInForm, FoodForm, WorkoutForm.
- [x] Client-side validation: required text fields, min/max constraints on numbers.
- [x] Error handling: error banner on API failures; disabled buttons while saving.
- [x] Tailwind + PostCSS configured (ESM).
- [x] Vite dev server with `/api` proxy to backend.
- [x] PWA manifest + basic service worker in public/.

## ✅ DevOps & Scripts
- [x] start-backend.ps1: Runs uvicorn from gymbro-api/.venv.
- [x] start-frontend.ps1: Installs deps (if needed), runs `npm run dev`.
- [x] start-all.ps1: Launches both in separate PowerShell windows.

## ✅ Documentation
- [x] Updated root README.md: quickstart, frontend notes, current data model, roadmap.
- [x] Updated gymbro-web/README.md: setup, build, structure, env, features.
- [x] .env.local in gymbro-web with VITE_USER_ID=1.

## 🧹 Cleanup Checklist

### Code Quality
- [ ] Remove console.logs / debug statements (none identified yet).
- [ ] Add JSDoc/docstrings to custom hooks / util functions (none custom yet).
- [ ] Ensure all imports are used (check for dead imports in all files).

### Backend
- [ ] Review routers for consistency (response formats, error handling).
- [ ] Add request validation errors to all endpoints (e.g., bad date format in PUT /daily-checkins/{date}).
- [ ] Verify CORS headers if frontend and backend run on different origins.
- [ ] Add 404 handling for missing resources (e.g., GET /workouts/{id} not found).

### Frontend
- [ ] Check for unused CSS classes in Tailwind build.
- [ ] Verify form reset after successful submission (currently does reset).
- [ ] Test mobile responsive layout (grid, form inputs).
- [ ] Confirm service worker registration in browser console.
- [ ] Add loading skeleton or spinner during initial data fetch (currently shows "Loading…" text).

### Database
- [ ] Verify indexes are appropriate (current schema has user_id, checkin_date, etc.).
- [ ] Add soft-delete support if needed (not in MVP scope).

### Testing
- [ ] Backend tests should cover edge cases (empty fields, negative numbers, bad user_id).
- [ ] Frontend e2e tests (Playwright or Cypress) for happy path: log check-in, meal, workout, refresh page, verify persistence.

### Config & Secrets
- [ ] .env.example in gymbro-web should document VITE_USER_ID.
- [ ] Ensure .env.local is in .gitignore (should be, check).

### Documentation
- [ ] Add inline comments to complex query logic in routers.
- [ ] Document API response schemas (can auto-gen from FastAPI /docs).
- [ ] Add troubleshooting section to README (schema mismatch, port conflicts, venv issues).

### Deployment Prep
- [ ] Add docker files (backend Dockerfile, frontend Dockerfile, docker-compose.yml).
- [ ] Add CI/CD workflow (GitHub Actions for tests).
- [ ] Document production env vars and secrets management.

## Notes
- Schema mismatch error (checkin_id column) was resolved by deleting stale gymbro.db; startup auto-creates fresh tables.
- All three main flows (check-in, meals, workouts) tested and working end-to-end.
- UI is minimal but fully functional; styling can be enhanced in later iterations.
