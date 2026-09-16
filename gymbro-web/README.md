# Gym Bro — Web Frontend

React 18 + Vite 5 + TypeScript + Tailwind PWA. See the [repo README](../README.md) for the
full stack and the [architecture doc](../docs/ARCHITECTURE.md) for system design.

## Development

Requires Node 20+. From the repo root, `./scripts/start-all.sh` runs the API and this app
together. To run only the frontend:

```bash
npm install
npm run dev
```

Visit `http://localhost:5173`. The dev server proxies `/api/*` to `http://localhost:8000`,
so the backend needs to be running for anything beyond the login screen.

## Environment

```bash
# gymbro-web/.env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

`VITE_API_URL` is optional in development — without it the client falls back to `/api` and
relies on the Vite proxy.

## Scripts

| Command | Does |
|---|---|
| `npm run dev` | Dev server with HMR |
| `npm run build` | Type-check and build to `dist/` |
| `npm run preview` | Serve the production build |
| `npm run test` | Vitest in watch mode |
| `npm run test:run` | Vitest once (46 tests) |
| `npm run coverage` | Vitest with a coverage report |
| `npm run lint` | ESLint, zero-warning policy |
| `npm run type-check` | `tsc --noEmit` |

## Structure

```
src/
├── main.tsx              Entry point, router
├── App.tsx               Shell and route definitions
├── contexts/
│   └── AuthContext.tsx   OAuth session state
├── pages/
│   ├── TodayPage.tsx     Daily check-in
│   ├── MealsPage.tsx     Meal logging, manual and from photo
│   ├── WorkoutPage.tsx   Workouts and exercise sets
│   ├── ProfilePage.tsx   User settings
│   ├── LoginPage.tsx     Google sign-in
│   └── AuthCallbackPage.tsx
├── components/
│   ├── BottomNav.tsx     Mobile navigation
│   ├── Forms.tsx         Check-in, food and workout forms
│   ├── PhotoCapture.tsx  Meal photo capture and quota display
│   ├── MealReview.tsx    Review and edit AI predictions before saving
│   └── OfflineIndicator.tsx
└── lib/
    ├── api.ts            Typed API client, cookie-based auth
    └── utils.ts          Date formatting, error handling
```

## Auth

Authentication is Google OAuth 2.0. The API sets a JWT in an httpOnly cookie, so the client
sends `credentials: 'include'` and never handles the token itself. A `401` from any request
redirects to `/login`.

## PWA

`public/manifest.json` and `public/sw.js` provide installability and a read-only offline
cache. Offline writes are not supported — `OfflineIndicator` tells the user when they are
disconnected.
