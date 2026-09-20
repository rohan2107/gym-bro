# Gym Bro

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/rohan2107/gym-bro/ci.yml?branch=main&label=ci)](https://github.com/rohan2107/gym-bro/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)

**Live Demo**: https://gym-bro-chi.vercel.app/

A full-stack fitness PWA with AI meal photo analysis, offline support, and a mobile-first UI. Built with FastAPI, React, and deployed on Vercel with CI/CD.

**Stack**: React · TypeScript · FastAPI · PostgreSQL · Google Cloud Vision · USDA API

## Features

✅ **AI meal logging** — photograph a meal, get food predictions and macros from Google
Vision + USDA, editable before saving (requires `GOOGLE_VISION_API_KEY` and `USDA_API_KEY`;
without them the services run in mock mode)  
✅ Google OAuth 2.0 authentication  
✅ Daily check-ins (weight, steps, training status)  
✅ Meal logging with calorie & macro tracking  
✅ Workout tracking with exercise sets  
✅ Mobile-first PWA with offline support  
✅ 225 automated tests, 85% backend coverage  
✅ CI/CD pipeline with GitHub Actions (8 required jobs + Vercel preview smoke test on PRs)

## Architecture

**Frontend**: React 18, TypeScript, Vite, Tailwind CSS  
**Backend**: FastAPI, SQLModel, Pydantic v2  
**Database**: PostgreSQL (Neon)  
**Auth**: Google OAuth 2.0 + JWT (httpOnly cookies)  
**AI**: Google Cloud Vision API + USDA FoodData Central  
**Hosting**: Vercel (frontend + serverless functions)  
**Testing**: pytest (175 tests), Vitest (50 tests), GitHub Actions

## Quick Start

Requires **Python 3.11+** and **Node 20+**.

```bash
# Backend
cd gymbro-api
python3.11 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head          # required: creates the schema
uvicorn app.main:app --reload

# Frontend
cd gymbro-web
npm install && npm run dev
```

Or start both at once: `./scripts/start-all.sh`

> **Note**: Alembic owns the schema. The app no longer creates tables at startup, so
> `alembic upgrade head` is required on a fresh database and after pulling new migrations.

Visit `http://localhost:5173` for the app and `http://localhost:8000/docs` for API docs.

### Environment Setup

Create `.env` files for local development:

**gymbro-api/.env**:
```bash
DATABASE_URL=postgresql://user:pass@localhost/gymbro
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
JWT_SECRET_KEY=your-jwt-secret
FRONTEND_URL=http://localhost:5173

# Optional: without these, photo analysis runs in mock mode
GOOGLE_VISION_API_KEY=your-vision-api-key
USDA_API_KEY=your-usda-api-key
```

All settings are declared in [gymbro-api/app/config.py](gymbro-api/app/config.py).

**gymbro-web/.env**:
```bash
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

See the [OAuth Setup Guide](docs/GOOGLE_OAUTH_SETUP.md) for Google OAuth configuration.

## Testing

```bash
# Backend (175 tests)
cd gymbro-api && pytest -v

# Frontend (50 tests)
cd gymbro-web && npm run test:run

# Full validation before committing
./scripts/pre-commit.sh        # Windows: .\scripts\pre-commit.ps1
```

## Linting

```bash
# Quick lint check (both backend & frontend)
./scripts/lint-check.sh        # Windows: .\scripts\lint-check.ps1

# Auto-fix lint issues
./scripts/lint-check.sh --fix  # Windows: .\scripts\lint-check.ps1 -Fix

# Manual linting
cd gymbro-api && ruff check --fix app/ tests/   # Backend (config in ruff.toml)
cd gymbro-web && npm run lint -- --fix          # Frontend
```

Shell scripts in [scripts/](scripts/) are the primary tooling; the matching `.ps1` files are
the Windows equivalents.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — System design, API endpoints, security model
- [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md) — Completed phases and product direction
- [AI Roadmap](docs/AI_ROADMAP.md) — Retrieval, agents and evaluation plan
- [All docs](docs/README.md) — Including OAuth setup and design specs

Contributing conventions, including the quality gates, are in [AGENTS.md](AGENTS.md).

## License

MIT — see [LICENSE](LICENSE)
