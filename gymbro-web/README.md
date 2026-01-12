# Gym Bro Web Frontend

React 18 + Vite 5 + TypeScript + TailwindCSS PWA. Logs fitness data: daily check-ins, meals, workouts.

## Setup & Dev

From repo root:

```bash
# Ensure backend env is set
python -m venv gymbro-api/.venv
./gymbro-api/.venv/Scripts/activate
pip install -r gymbro-api/requirements.txt

# Frontend env
Set-Content -Path gymbro-web/.env.local -Value "VITE_USER_ID=1"
cd gymbro-web
npm install
npm run dev
```

Visit `http://localhost:5173`. The dev server proxies `/api/*` to `http://127.0.0.1:8000`.

### With Scripts

From repo root:

```powershell
# Backend + frontend in separate terminals
powershell -ExecutionPolicy Bypass -File scripts/start-all.ps1

# Or individually:
powershell -ExecutionPolicy Bypass -File scripts/start-backend.ps1
powershell -ExecutionPolicy Bypass -File scripts/start-frontend.ps1
```

## Build & Preview

```bash
npm run build
npm run preview
```

## Structure

- `src/main.tsx` — Entry point.
- `src/App.tsx` — Main app component (daily check-in, meals, workouts).
- `src/lib/api.ts` — API client with X-User-Id header.
- `src/components/Forms.tsx` — Form components (check-in, food, workout).
- `src/index.css` — Global styles (Tailwind).
- `public/manifest.json` — PWA manifest.
- `public/sw.js` — Service Worker (basic offline support).

## Env

- `VITE_USER_ID` — User ID for X-User-Id header (defaults to `1` if not set).

## Features (MVP)

- **Daily Check-in**: Log weight, steps, trained, protein met, notes. Upsert via PUT.
- **Meals**: Log description + optional calories. List shows newest first.
- **Workouts**: Log name + optional note. List shows newest first.
- Error banner on API failures; disabled buttons while saving.
