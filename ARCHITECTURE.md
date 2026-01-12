# Architecture & Technical Decisions

**Last Updated**: January 12, 2026

---

## 🏗️ System Architecture

### Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | React 18 + Vite + TypeScript | Modern, fast, responsive |
| **Mobile** | PWA + Tailwind + Service Worker | Works offline, installable |
| **Backend** | FastAPI + SQLModel | Async, type-safe, fast |
| **Database** | PostgreSQL (Neon) | Scalable, relational, free tier |
| **Auth** | Google OAuth 2.0 + JWT | Industry standard, secure |
| **Hosting** | Vercel (frontend + functions) | Free tier, auto-deploy, simple |
| **Storage** | Vercel Blob | Free, integrated, simple |
| **AI/Vision** | Google Cloud Vision API | Food detection, free tier |
| **Testing** | pytest (backend) + Playwright (E2E) | Comprehensive coverage |
| **CI/CD** | GitHub → Vercel | Automatic on push |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User (Phone)                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Vercel CDN (Frontend Static)                    │
│         React 18 + Vite + TypeScript + Tailwind             │
│  ├─ Check-in card                                           │
│  ├─ Meals logging (+ photo capture)                         │
│  ├─ Workouts logging                                        │
│  └─ Analytics dashboard                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓ /api
┌─────────────────────────────────────────────────────────────┐
│            Vercel Functions (Backend Serverless)             │
│        FastAPI + SQLModel + Pydantic v2                     │
│  ├─ /health                      [status check]             │
│  ├─ /auth/google/callback        [OAuth flow]               │
│  ├─ /daily-checkins              [CRUD]                     │
│  ├─ /food-logs                   [CRUD + photo]             │
│  ├─ /workouts                    [CRUD]                     │
│  ├─ /exercise-sets               [CRUD]                     │
│  ├─ /weight-entries              [CRUD]                     │
│  └─ /analytics                   [aggregations]             │
└─────────────────────────────────────────────────────────────┘
            ↓                    ↓                   ↓
    ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐
    │ Neon PostgreSQL│ │  Vercel Blob     │  │ Google Cloud │
    │   Database     │ │ Photo Storage    │  │ Vision API   │
    │ (3 GB free)    │ │ (1 GB free)      │  │ (1000/mo)    │
    └──────────────┘  └──────────────────┘  └──────────────┘
```

---

## 🔑 Key Decisions

### 1. Backend: Vercel Functions vs. Traditional Server

**Decision**: Vercel Functions (serverless)

**Trade-offs**:
| Aspect | Vercel Functions | Traditional Server (Railway) |
|--------|------------------|--------------------------|
| Cost | $0 free tier | $5–7/month |
| Cold starts | 1–5 sec first call | Always warm |
| Setup | Simple (same platform) | Separate service |
| Scaling | Automatic | Manual |
| Best for | MVP, personal use | Production scale |

**Why Functions for MVP**: Free tier covers personal usage; complexity can upgrade later.

---

### 2. Database: Neon PostgreSQL vs. SQLite vs. Supabase

**Decision**: Neon PostgreSQL

**Why**:
- Free tier: 3 GB storage, 3 projects, shared compute
- Serverless-compatible (works with Vercel Functions)
- Standard PostgreSQL (no vendor lock-in)
- Easy backups
- Upgrade path to production ($15/month for generous tier)

**Alternatives considered**:
- **SQLite**: Easy locally but doesn't persist on Vercel (ephemeral storage)
- **Supabase**: Also good, but more expensive ($25/month), includes auth (we use Google)

---

### 3. Photo Storage: Vercel Blob vs. Google Cloud vs. AWS S3

**Decision**: Vercel Blob

**Why**:
- Free tier: 1 GB, 1000 requests/month (covers ~30 photos/day)
- Integrated with Vercel (same dashboard)
- Simpler than Google Cloud Storage setup
- One less service to manage

**Cost breakdown**:
- Vercel Blob: $0 (free tier)
- Google Cloud Vision: $0.50/100 requests (free: 1000/month)
- Total: $0/month for MVP

**Rate limiting**:
- **Free tier limit**: 1000 requests/month (~33/day)
- **Implementation**: Client-side debounce (500ms), backend request counter
- **User messaging**: Show "X photos remaining today" + upgrade prompt
- **Fallback**: Auto-switch to manual entry if quota exceeded
- **Monitoring**: Track usage via Google Cloud Console alerts

---

### 4. Authentication: OAuth vs. Session vs. JWT

**Decision**: Google OAuth 2.0 + JWT

**Why**:
- **Google OAuth**: No password management, secure, standard
- **JWT tokens**: Stateless, work with serverless, mobile-friendly
- **httpOnly cookies**: Secure storage (CSRF protected)

**Flow**:
1. User clicks "Sign in with Google"
2. Google redirects with ID token
3. Backend verifies token with Google, creates User, returns JWT
4. Frontend stores JWT in localStorage/cookie
5. All API calls include `Authorization: Bearer <token>`

---

### 5. Hosting: Vercel vs. Heroku vs. DigitalOcean vs. Self-Hosted

**Decision**: Vercel

**Why**:
- Free tier (unlimited static sites, 100k functions/month)
- Automatic deployment (GitHub → Vercel on push)
- Built-in monitoring, logs, analytics
- Integrates with PostgreSQL (Neon)
- Fast CDN for frontend
- Suitable for personal + showcase project

**Cost**: $0/month (free tier covers MVP)

---

### 6. AI Vision: Google Cloud Vision vs. OpenAI vs. On-Device

**Decision**: Google Cloud Vision

**Why**:
- Integrates naturally with Google OAuth (same ecosystem)
- Good food detection accuracy
- Free tier: 1000 requests/month
- API is well-documented
- Cost: $0 for MVP usage

**Alternatives**:
- **OpenAI Vision**: $0.01/image (expensive for frequent photos)
- **On-device TensorFlow**: Privacy but lower accuracy
- **Clarifai**: Food-specific but smaller community

---

## 🛡️ Security & Risk Assessment

### Security Measures

| Risk | Mitigation |
|------|-----------|
| Unauth API access | JWT validation on all endpoints |
| CSRF attacks | httpOnly cookies + CORS |
| User data leakage | Row-level security (filter by user_id) |
| Token theft | Short expiry (7 days), refresh tokens |
| Photo exposure | Private storage, presigned URLs |
| SQL injection | SQLModel + SQLAlchemy (parameterized) |

### Verified Protections

- ✅ User isolation: Tested (user 1 can't see user 2's data)
- ✅ CORS: Configured for Vercel domain
- ✅ JWT validation: Checked on all protected endpoints
- ✅ Database: Automatic SSL (Neon)
- ✅ API authentication: OAuth 2.0 (industry standard)

---

## ⚠️ Known Limitations & Future Upgrades

### Current Limitations

| Limitation | Impact | When to Fix |
|-----------|--------|-----------|
| Cold starts (1–5s) | First request slower | If production scale required |
| 10s timeout (Vercel) | Long operations fail | If batch processing needed |
| 1 GB Blob storage | ~1000 photos max | After user base grows |
| Shared compute (Neon) | Potential slowness | If peak load increases |

### Upgrade Path

| Milestone | Action | Cost |
|-----------|--------|------|
| MVP (now) | Current stack | $0/month |
| Private beta (10 users) | Monitor performance | $0/month |
| Public launch (100+ users) | Upgrade Neon + Blob | $20–30/month |
| Scale (1000+ users) | Dedicated backend + DB | $50–200/month |

---

## 📊 Tech Stack Maturity

| Component | Maturity | Production Ready |
|-----------|----------|-----------------|
| React 18 | ✅ Stable | Yes |
| FastAPI | ✅ Stable | Yes |
| PostgreSQL | ✅ Enterprise | Yes |
| Google OAuth | ✅ Industry standard | Yes |
| Vercel | ✅ Mature platform | Yes |
| Tailwind | ✅ Stable | Yes |
| TypeScript | ✅ Stable | Yes |

**Overall**: All production-grade technologies.

---

## 🎓 Skills Gained by Phase

| Phase | Skills |
|-------|--------|
| 1A (Mobile UX) | React patterns, Tailwind, PWA, responsive design |
| 1B (Vercel) | Serverless deployment, PostgreSQL, CI/CD |
| 2 (OAuth) | Google Cloud, OAuth 2.0, JWT, multi-tenant design |
| 3A (Stabilization) | Testing, monitoring, performance optimization |
| 3B (AI) | Vision API, image processing, ML integration |

---

## 🚀 Performance & Scalability

### Current Performance Targets

| Metric | Target | Method |
|--------|--------|--------|
| Page load | <2s | Vite + CDN |
| API response | <200ms | FastAPI async |
| PWA score | >90 | Service worker + caching |
| Database query | <100ms | PostgreSQL indexes |
| Cold start | <5s | Acceptable for MVP |

### Scalability (Future)

To handle 1000+ users:
- [ ] Migrate backend to dedicated server (Railway $7/mo)
- [ ] Upgrade database (Neon $15/mo)
- [ ] Add caching (Redis)
- [ ] Add CDN image serving (Cloudflare)
- [ ] Database replication/backups

---

## 📋 Deployment Checklist (Before Production)

- [ ] HTTPS enabled (automatic on Vercel)
- [ ] CORS configured for production domain
- [ ] Environment secrets stored securely (Vercel Secrets)
- [ ] Database backups automated (Neon)
- [ ] Monitoring set up (Vercel logs + error tracking)
- [ ] Rate limiting configured (if needed)
- [ ] Input validation hardened (already done)
- [ ] CSRF protection enabled (httpOnly cookies)
- [ ] Data retention policy documented
- [ ] Privacy policy written

---

## 🔗 Related Documentation

- **IMPLEMENTATION_ROADMAP.md**: 12-week plan
- **DEPLOYMENT_GUIDE.md**: Step-by-step Vercel setup
- **GOOGLE_OAUTH_SETUP.md**: OAuth implementation
- **MOBILE_UI_SPEC.md**: Frontend design specifications

---

## 📞 Questions?

Each technical decision above has trade-offs. If you want to:
- **Change backend to dedicated server**: Possible, adds $5–7/month cost
- **Change to different OAuth provider**: Doable, similar effort
- **Upgrade to Supabase**: Works, but different setup
- **Add Stripe for payments**: Easy (separate service)

All decisions are reversible. Start with current stack, upgrade as needed.
