# MVP Status

**Status**: ✅ Deployed & Operational (January 19, 2026)  
**Live URL**: https://gym-ba2oz8etc-rohan-anthonys-projects-a86489a8.vercel.app

## Production Summary

| Component | Status | Details |
|-----------|--------|---------|
| Frontend | ✅ Deployed | React + Vite PWA on Vercel |
| Backend | ✅ Deployed | FastAPI on Vercel Functions, PostgreSQL (Neon) |
| Mobile UI | ✅ Complete | Bottom nav, 4 pages, responsive layout |
| Offline Support | ✅ Complete | Service worker with cache strategy |
| DevOps | ✅ Complete | GitHub → Vercel auto-deploy |

## Features

✅ **Daily Check-ins** - Track weight, steps, training status, protein intake with date navigation  
✅ **Meal Logging** - Full CRUD with calorie/macro tracking  
✅ **Workout Tracking** - Create, edit, delete workouts with notes  
✅ **Mobile-First PWA** - Bottom navigation, install to home screen, offline support  
✅ **Data Persistence** - PostgreSQL backend with automatic backups  
✅ **Responsive Design** - Optimized for mobile, tablet, desktop

## Technical Stack

**Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Service Worker  
**Backend**: FastAPI, SQLModel, Pydantic v2, PostgreSQL (Neon)  
**Deployment**: Vercel (frontend + serverless backend), GitHub CI/CD  
**Authentication**: Temporary X-User-Id header (OAuth planned for Phase 2)

## Known Limitations

⚠️ **Single User Mode**: All users currently share data (user ID 1)  
⚠️ **No Real Auth**: Using header-based authentication temporarily  
⚠️ **Public Data**: No user isolation until OAuth is implemented

## Next Phase: Google OAuth Authentication

**Goal**: Enable real user authentication and multi-user support

**Key Deliverables**:
- Google OAuth 2.0 integration
- JWT token-based authentication  
- User data isolation (each user sees only their data)
- Login/logout flow with protected routes
- Migration from X-User-Id to real user sessions

See [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) and [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md) for implementation details.

## Future Phases

**Phase 3A-3B**: Testing & AI meal photo logging
- Comprehensive test coverage (unit, integration, E2E)
- Google Cloud Vision API integration
- Automatic meal detection from photos

**Phase 3C**: Energy balance & analytics
- TDEE estimation (Mifflin-St Jeor + adaptive learning)
- Strong app workout import with LLM calorie estimation
- Energy balance tracking and analytics dashboard
- Multi-hypothesis discrepancy analysis
- Science-based weight loss validation

See [ENERGY_BALANCE_SPEC.md](ENERGY_BALANCE_SPEC.md) for detailed specification.

## Local Development

See [README.md](README.md) for complete setup instructions.

**Quick Start**:
```bash
# Backend
cd gymbro-api && uvicorn app.main:app --reload

# Frontend  
cd gymbro-web && npm run dev
```

Visit `http://localhost:5173` for the app and `http://localhost:8000/docs` for API documentation.
