# Gym Bro

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/rohan2107/gym-bro/ci.yml?branch=main&label=ci)](https://github.com/rohan2107/gym-bro/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)

**Live Demo**: https://gym-bro-chi.vercel.app/

A full-stack fitness PWA with AI meal photo analysis, offline support, and a mobile-first UI. Built with FastAPI, React, and deployed on Vercel with CI/CD.

**Stack**: React · TypeScript · FastAPI · PostgreSQL · Google Cloud Vision · USDA API

## Features

✅ **AI meal logging** — snap a photo, get calories & macros via Google Vision + USDA  
✅ Google OAuth 2.0 authentication  
✅ Daily check-ins (weight, steps, training status)  
✅ Meal logging with calorie & macro tracking  
✅ Workout tracking with exercise sets  
✅ Mobile-first PWA with offline support  
✅ 160 automated tests, 84% backend coverage  
✅ CI/CD pipeline with GitHub Actions (7 parallel jobs)

## Architecture

**Frontend**: React 18, TypeScript, Vite, Tailwind CSS  
**Backend**: FastAPI, SQLModel, Pydantic v2  
**Database**: PostgreSQL (Neon)  
**Auth**: Google OAuth 2.0 + JWT (httpOnly cookies)  
**AI**: Google Cloud Vision API + USDA FoodData Central  
**Hosting**: Vercel (frontend + serverless functions)  
**Testing**: pytest (133 tests), Vitest (27 tests), GitHub Actions

## Quick Start

```bash
# Backend
cd gymbro-api
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd gymbro-web
npm install && npm run dev
```

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
```

**gymbro-web/.env**:
```bash
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

See [OAuth Setup Guide](docs/archive/GOOGLE_OAUTH_SETUP.md) for Google OAuth configuration.

## Testing

```bash
# Backend (133 tests)
cd gymbro-api && pytest -v

# Frontend (27 tests)
cd gymbro-web && npm run test:run

# Full validation before committing
.\scripts\pre-commit.ps1
```

## Linting

```bash
# Quick lint check (both backend & frontend)
.\scripts\lint-check.ps1

# Auto-fix lint issues
.\scripts\lint-check.ps1 -Fix

# Manual linting
cd gymbro-api && ruff check --fix .    # Backend
cd gymbro-web && npm run lint -- --fix  # Frontend
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — System design, API endpoints, security model
- [Roadmap](docs/IMPLEMENTATION_ROADMAP.md) — Development phases and upcoming features

## License

MIT — see [LICENSE](LICENSE)
