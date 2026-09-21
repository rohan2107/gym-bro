# Gym Bro

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/rohan2107/gym-bro/ci.yml?branch=main&label=ci)](https://github.com/rohan2107/gym-bro/actions)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://python.org)

**Live Demo**: https://gym-bro-chi.vercel.app/

A full-stack fitness PWA with AI meal photo analysis, offline support, and a mobile-first UI. Built with FastAPI, React, and deployed on Vercel with CI/CD.

**Stack**: React · TypeScript · FastAPI · PostgreSQL · Gemini API · USDA API

## Features

✅ **AI meal photo analysis** — photograph a meal, get food predictions and macros, editable
before saving. Foods are recognised by the Gemini API (free tier, no billing account) and
looked up in USDA; the provider is swappable by configuration. **Enabled on the live site once
`GEMINI_API_KEY` is set there**; locally it runs in mock mode without keys. Nutrition is per
100g until portion estimates land ([roadmap](docs/ROADMAP.md#m03b-portions))  
✅ Google OAuth 2.0 authentication  
✅ Daily check-ins (weight, steps, training status)  
✅ Meal logging with calorie & macro tracking  
✅ Workout tracking with exercise sets  
✅ Mobile-first PWA with offline support  
✅ 334 automated tests, 88% backend coverage  
✅ CI/CD pipeline with GitHub Actions (8 required jobs + Vercel preview smoke test on PRs)

## Architecture

**Frontend**: React 18, TypeScript, Vite, Tailwind CSS  
**Backend**: FastAPI, SQLModel, Pydantic v2  
**Database**: PostgreSQL (Neon)  
**Auth**: Google OAuth 2.0 + JWT (httpOnly cookies)  
**AI**: Gemini API (food recognition) + USDA FoodData Central  
**Hosting**: Vercel (frontend + serverless functions)  
**Testing**: pytest (254 tests), Vitest (80 tests), GitHub Actions

## Quick Start

Requires **Python 3.12** and **Node 24** (pinned in `.python-version` and `.nvmrc`).

```bash
# Backend
cd gymbro-api
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
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
GEMINI_API_KEY=your-gemini-api-key        # https://aistudio.google.com, free tier
USDA_API_KEY=your-usda-api-key
# FOOD_RECOGNITION_PROVIDER=vision        # optional; needs GOOGLE_VISION_API_KEY and billing
```

All settings are declared in [gymbro-api/app/config.py](gymbro-api/app/config.py).

**gymbro-web/.env** (optional; without it the client uses `/api` through the Vite proxy):
```bash
VITE_API_URL=http://localhost:8000
```

See [Authentication](docs/AUTHENTICATION.md) for Google OAuth setup, including the redirect
URI to register.

## Testing

```bash
# Backend (254 tests)
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

## Direction

The app is being extended into a system whose LLM behaviour is measured, observable and
resilient: retrieval with citations, an evaluation harness gated in CI, tracing, and then an
agent with tools. Everything runs on free tiers that stop at their limit rather than bill. The
plan, its sequence and its risks are in the [roadmap](docs/ROADMAP.md).

## Documentation

- [Architecture](docs/ARCHITECTURE.md): system design, API endpoints, security model, testing
- [Roadmap](docs/ROADMAP.md): planned work, sequenced into reviewable milestones
- [Deployment](docs/DEPLOYMENT.md): configuration, CI/CD, releasing and rollback
- [Decision records](docs/adr/README.md): what was decided and why
- [All docs](docs/README.md)

Contribution conventions, including the quality gates, are in [AGENTS.md](AGENTS.md). Changes
are recorded in the [changelog](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE)
