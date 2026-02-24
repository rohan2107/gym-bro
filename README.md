# Gym Bro

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/rohan2107/gym-bro/ci.yml?label=ci)](https://github.com/rohan2107/gym-bro/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)

**Live Demo**: https://gym-bro-chi.vercel.app/

A production-ready fitness PWA for tracking nutrition and workouts. Built with modern web technologies, deployed on Vercel with full CI/CD.

**Stack**: React · TypeScript · FastAPI · PostgreSQL · Google OAuth 2.0

## Features

✅ Google OAuth 2.0 authentication  
✅ Daily check-ins (weight, steps, training status)  
✅ Meal logging with calorie & macro tracking  
✅ Workout tracking with exercise sets  
✅ Mobile-first PWA with offline support  
✅ 74 automated tests with 85% coverage  
✅ CI/CD pipeline with GitHub Actions

## Architecture

**Frontend**: React 18, TypeScript, Vite, Tailwind CSS  
**Backend**: FastAPI, SQLModel, Pydantic v2  
**Database**: PostgreSQL (Neon)  
**Auth**: Google OAuth 2.0 + JWT (httpOnly cookies)  
**Hosting**: Vercel (frontend + serverless functions)  
**Testing**: pytest, Vitest, GitHub Actions

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
# Backend (47 tests)
cd gymbro-api && pytest -v

# Frontend (27 tests)
cd gymbro-web && npm run test:run

# Or for watch mode during development:
# cd gymbro-web && npm test
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

- [Architecture](docs/ARCHITECTURE.md) — System design and technical decisions
- [Testing Guide](docs/TESTING_GUIDE.md) — Test suite and quality gates
- [OAuth Setup](docs/archive/GOOGLE_OAUTH_SETUP.md) — Google OAuth 2.0 configuration (archived)
- [Roadmap](docs/IMPLEMENTATION_ROADMAP.md) — Development phases and upcoming features

## License

MIT — see [LICENSE](LICENSE)
