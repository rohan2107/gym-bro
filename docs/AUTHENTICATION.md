# Authentication

Sign-in uses Google OAuth 2.0 (authorization code flow). The API issues its own session token
as an httpOnly cookie. This document covers setup, the flow as implemented, the session model,
and the known gaps.

## Setup

1. In the [Google Cloud console](https://console.cloud.google.com/) choose or create a project,
   then configure the **OAuth consent screen**. While the app is in *Testing* status only
   accounts listed as test users can sign in.
2. Under **APIs & Services → Credentials**, create an **OAuth client ID** of type **Web
   application**.
3. Add **Authorized redirect URIs**. The redirect is to the *frontend*, and must match
   `<FRONTEND_URL>/auth/callback` exactly, including scheme and port:

   | Environment | Redirect URI |
   |---|---|
   | Local | `http://localhost:5173/auth/callback` |
   | Production | `https://<your-domain>/auth/callback` |

4. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` and `FRONTEND_URL` for the backend
   ([DEPLOYMENT.md](DEPLOYMENT.md#configuration)). `FRONTEND_URL` must equal the origin the
   user is actually on, because the callback URI is derived from it.

Creating this client does not involve a billing account.

## The flow

```
Browser                      Frontend                 API                          Google
   |  click "Sign in"           |                       |                             |
   |--------------------------->| GET /api/auth/google/login                          |
   |                            |---------------------->| 307 to Google's auth URL    |
   |<------------------------------------------------------------------------------- |
   |  user authenticates and consents                                                 |
   |------------------------------------------------------------------------------->  |
   |  redirect to <FRONTEND_URL>/auth/callback?code=...                               |
   |--------------------------->|                       |                             |
   |                            | GET /api/auth/google/callback?code=...              |
   |                            |---------------------->| POST token endpoint         |
   |                            |                       |---------------------------->|
   |                            |                       | verify ID token             |
   |                            |                       | find or create the user     |
   |                            | 200, Set-Cookie: auth_token                         |
   |                            |<----------------------|                             |
   |  navigate to /profile      |                       |                             |
```

The requested scopes are `openid email profile`.

### Accounts

The user is found by Google subject id, then by email. Matching by email links an account
created before its Google id was recorded. New users are created on first sign-in; there is no
separate sign-up.

## Sessions

| Property | Value |
|---|---|
| Token | JWT, HS256, signed with `JWT_SECRET_KEY`, 7-day expiry |
| Cookie | `auth_token`; `HttpOnly`, `SameSite=Lax`, `Secure` when `FRONTEND_URL` is `https` |
| Also accepted | `Authorization: Bearer <token>`, for non-browser clients |
| Identity | `get_user_id()` extracts the user id; every query filters by it |

An unset `JWT_SECRET_KEY` makes token creation raise; the app never signs with an empty key.

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/auth/google/login` | Redirects to Google |
| `GET` | `/api/auth/google/callback` | Exchanges the code, sets the cookie |
| `GET` | `/api/auth/me` | The current user |
| `POST` | `/api/auth/logout` | Clears the cookie |

## The development header

`X-User-Id: <n>` authenticates a request as user *n* with no credentials. It exists for local
development and tests only, and it is the mechanism behind [AUDIT F12](AUDIT_2026-09.md).

It is enabled only when `ENVIRONMENT` is explicitly `development` or `test`. The setting
defaults to `production`, and the header is **never** accepted on Vercel (`VERCEL` is set),
whatever `ENVIRONMENT` says. Do not widen those conditions.

## Known gaps

Recorded as open findings in the [audit](AUDIT_2026-09.md#open-findings):

- **No `state` parameter** (O1): the login flow is exposed to login CSRF
- **`email_verified` is not checked** before linking an account by email (O2)
- **Raw provider error text** is returned to the client when the token exchange fails (O3)
- **The callback page runs its effect twice in development** (O4): the second request reuses a
  single-use code and returns `400`. Harmless, and absent from a production build.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Google shows `redirect_uri_mismatch` | The redirect URI in the console does not exactly match `<FRONTEND_URL>/auth/callback` |
| "Google OAuth not configured" (500) | `GOOGLE_CLIENT_ID` or `GOOGLE_CLIENT_SECRET` is unset |
| Sign-in loops back to the login page | The cookie was not stored: check `FRONTEND_URL`, and whether the site is on `https` |
| Access blocked for a valid account | The consent screen is in Testing status and the account is not a listed test user |
| `400` from the callback in local development | The double-fired effect (O4), if sign-in otherwise succeeded |
| `401` on every request | Missing or expired cookie, or `JWT_SECRET_KEY` changed since it was issued |
