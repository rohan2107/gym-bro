# Phase 2: OAuth Implementation Plan (Refined)

**Timeline**: 4-6 hours  
**Date**: January 19, 2026

---

## 🎯 Overview
Replace temporary `X-User-Id` header with production-ready Google OAuth using modern best practices.

---

## Part 1: Google Cloud Setup (30 mins)

### 1.1 Create Google Cloud Project
- [ ] Go to https://console.cloud.google.com
- [ ] Create new project: "Gym Bro"
- [ ] Wait for creation (~1 minute)

### 1.2 Enable Google Identity Services
- [ ] Navigate to "APIs & Services" → "Library"
- [ ] Search for "Google Identity Services API"
- [ ] Click "Enable"
- [ ] **Note**: Using OAuth 2.0 / OpenID Connect (NOT deprecated Google+ API)

### 1.3 Configure OAuth Consent Screen
- [ ] Go to "APIs & Services" → "OAuth consent screen"
- [ ] User Type: External
- [ ] App name: "Gym Bro"
- [ ] User support email: your email
- [ ] Scopes: `openid`, `profile`, `email`
- [ ] Developer contact: your email
- [ ] Save

### 1.4 Create OAuth Credentials
- [ ] Go to "APIs & Services" → "Credentials"
- [ ] Click "Create Credentials" → "OAuth 2.0 Client ID"
- [ ] Application type: "Web application"
- [ ] Name: "Gym Bro Web Client"
- [ ] Authorized redirect URIs:
  - `http://localhost:5173/auth/callback` (development)
  - `https://gym-ba2oz8etc-rohan-anthonys-projects-a86489a8.vercel.app/auth/callback` (production)
- [ ] Download credentials (client ID + secret)

### 1.5 Store Credentials Securely
```bash
# gymbro-api/.env (local - NEVER COMMIT)
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
JWT_SECRET_KEY=generate_with_openssl_rand_hex_32
FRONTEND_URL=http://localhost:5173

# Vercel Environment Variables (production)
# Add same variables in Vercel dashboard → Settings → Environment Variables
```

---

## Part 2: Backend Implementation (2-3 hours)

### 2.1 Database Schema Updates

**Update User Model** (`gymbro-api/app/models.py`):
```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)  # Add unique constraint
    google_id: str = Field(unique=True, index=True)  # NEW
    display_name: Optional[str] = None
    picture_url: Optional[str] = None  # NEW
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
```

**Alembic Migration**:
- [ ] Install Alembic: `pip install alembic`
- [ ] Initialize: `alembic init alembic` (if not exists)
- [ ] Create migration: `alembic revision -m "add_google_auth_fields"`
- [ ] Edit migration file to add `google_id`, `picture_url`, make `email` unique
- [ ] Test locally: `alembic upgrade head`
- [ ] Run on Neon production (via connection string)

**Why Alembic**: Keeps migrations version-controlled and repeatable (production-grade approach)

### 2.2 Install Dependencies

**Add to `requirements.txt`**:
```
python-jose[cryptography]  # JWT creation/validation
google-auth                 # Google ID token verification
python-multipart           # OAuth form handling
alembic                    # Database migrations
```

**Install**: `pip install -r requirements.txt`

### 2.3 JWT Utilities (`gymbro-api/app/auth_utils.py`)

```python
from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError
from fastapi import HTTPException, status
import os

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7

def create_jwt(user_id: int) -> str:
    """Generate JWT token with 7-day expiration"""
    expire = datetime.now(UTC) + timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(UTC)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt(token: str) -> int:
    """Validate JWT and return user_id, raise 401 if invalid/expired"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
```

**Design Decision**: No refresh tokens in Phase 2
- **Why**: Simpler implementation, 7-day expiry is reasonable for MVP
- **Future**: Add refresh tokens in Phase 4 when adding offline sync
- **Tradeoff**: Users must re-login weekly (acceptable for fitness tracking app)

### 2.4 Auth Router (`gymbro-api/app/routers/auth.py`)

**Routes** (future-proof naming):
- `GET /auth/login` - Redirect to Google OAuth (currently Google, but extensible)
- `GET /auth/callback` - Handle OAuth response
- `POST /auth/logout` - Clear auth cookie
- `GET /auth/me` - Get current authenticated user (validates JWT expiry)

**Cookie Security Settings**:
```python
from fastapi import Response

def set_auth_cookie(response: Response, token: str, is_production: bool):
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,           # Prevent XSS
        secure=is_production,    # HTTPS only in production
        samesite="lax",          # CSRF protection (allows top-level navigation)
        max_age=7 * 24 * 60 * 60,  # 7 days (matches JWT expiration)
        domain=None if not is_production else ".vercel.app"  # Vercel subdomain handling
    )
```

**Implementation Details**:
- [ ] `GET /auth/login`: Generate Google OAuth URL, redirect user
- [ ] `GET /auth/callback`: 
  - Exchange auth code for ID token
  - Verify ID token with Google
  - Create/update User in database
  - Generate JWT
  - Set secure cookie
  - Redirect to frontend
- [ ] `POST /auth/logout`: Delete cookie, return 200
- [ ] `GET /auth/me`: 
  - Extract JWT from cookie
  - Validate (auto-checks expiry via `verify_jwt`)
  - Return user data
  - **On expiry**: Returns 401 (frontend redirects to login)

### 2.5 Update Dependency Injection (`gymbro-api/app/deps.py`)

**Replace `get_user_id()` implementation**:
```python
from fastapi import Cookie, HTTPException, status
from app.auth_utils import verify_jwt

def get_user_id(auth_token: str = Cookie(None)) -> int:
    """Extract and validate user_id from JWT cookie"""
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return verify_jwt(auth_token)  # Raises 401 if expired/invalid
```

**Migration Strategy** (optional):
- Keep backward compatibility temporarily (accept X-User-Id OR cookie)
- Remove X-User-Id support after confirming OAuth works

### 2.6 Update Main App (`gymbro-api/app/main.py`)

```python
from app.routers import auth

app.include_router(auth.router, prefix="/auth", tags=["auth"])
```

---

## Part 3: Frontend Implementation (1-2 hours)

### 3.1 Auth Context (`gymbro-web/src/contexts/AuthContext.tsx`)

```typescript
type User = {
  id: number
  email: string
  display_name: string | null
  picture_url: string | null
}

type AuthContextType = {
  user: User | null
  isLoading: boolean
  login: () => void
  logout: () => Promise<void>
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check auth status on mount
  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/auth/me', { credentials: 'include' })
      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      }
    } catch (error) {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  const login = () => {
    window.location.href = '/api/auth/login'
  }

  const logout = async () => {
    await fetch('/api/auth/logout', { 
      method: 'POST', 
      credentials: 'include' 
    })
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
```

### 3.2 Login Page (`gymbro-web/src/pages/LoginPage.tsx`)

```typescript
export default function LoginPage() {
  const { login } = useAuth()

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8">
        <h1 className="text-3xl font-bold text-center">Gym Bro</h1>
        <button
          onClick={login}
          className="w-full flex items-center justify-center gap-3 bg-white border border-gray-300 rounded-lg px-6 py-3 hover:bg-gray-50"
        >
          <img src="https://www.google.com/favicon.ico" alt="Google" className="w-5 h-5" />
          Sign in with Google
        </button>
      </div>
    </div>
  )
}
```

### 3.3 Update API Client (`gymbro-web/src/lib/api.ts`)

**Changes**:
- [ ] Remove `const USER_ID = '1'`
- [ ] Remove `'X-User-Id': USER_ID` from headers
- [ ] Add `credentials: 'include'` to all fetch calls (sends cookies)
- [ ] Handle 401 responses → redirect to `/login`

```typescript
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include',  // Send cookies
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  })

  if (res.status === 401) {
    // JWT expired or invalid - redirect to login
    window.location.href = '/login'
    throw new Error('Authentication required')
  }

  if (!res.ok) {
    const message = await res.text()
    throw new Error(message || `Request failed (${res.status})`)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}
```

### 3.4 Protected Routes (`gymbro-web/src/App.tsx`)

```typescript
function App() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (!user) {
    return <LoginPage />
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<TodayPage />} />
        <Route path="/meals" element={<MealsPage />} />
        <Route path="/workout" element={<WorkoutPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Routes>
      <BottomNav />
    </Router>
  )
}
```

### 3.5 Update Profile Page (`gymbro-web/src/pages/ProfilePage.tsx`)

```typescript
const { user, logout } = useAuth()

return (
  <div>
    <img src={user.picture_url} alt={user.display_name} className="w-16 h-16 rounded-full" />
    <p>{user.email}</p>
    <button onClick={logout}>Sign Out</button>
  </div>
)
```

---

## Part 4: Testing & Verification (30-60 mins)

### 4.1 Local Testing
- [ ] Start backend: `cd gymbro-api && uvicorn app.main:app --reload`
- [ ] Start frontend: `cd gymbro-web && npm run dev`
- [ ] Visit http://localhost:5173
- [ ] Click "Sign in with Google"
- [ ] Verify redirect to Google login
- [ ] Approve permissions
- [ ] Verify redirect back to app
- [ ] Check browser DevTools → Application → Cookies (should see `auth_token`)
- [ ] Create check-in, meal, workout
- [ ] Verify data persists after page refresh

### 4.2 Multi-User Testing
- [ ] Sign out
- [ ] Clear cookies
- [ ] Sign in with DIFFERENT Google account
- [ ] Verify no data from first user visible
- [ ] Create new data as second user
- [ ] Sign out and back in as first user
- [ ] Verify data isolation is working

### 4.3 JWT Expiration Testing
- [ ] In `auth_utils.py`, temporarily set `JWT_EXPIRATION_DAYS = 1/1440` (1 minute)
- [ ] Sign in, verify auth works
- [ ] Wait 2 minutes
- [ ] Try to make API call
- [ ] Should get 401, redirect to login
- [ ] Change back to 7 days

### 4.4 Production Deployment
- [ ] Run Alembic migration on Neon production database
- [ ] Update Vercel environment variables (Client ID, Secret, JWT key)
- [ ] Push to GitHub (triggers Vercel deploy)
- [ ] Test full OAuth flow on production URL
- [ ] Verify cookie security settings (DevTools → Application → Cookies → Secure: true)

---

## Part 5: Cleanup (15 mins)

- [ ] Remove all `TODO: replace with real auth` comments
- [ ] Delete temporary `X-User-Id` code (if fully migrated)
- [ ] Update README.md:
  - Add "Authentication" section
  - Document required environment variables
  - Show how to set up local `.env` file
- [ ] Add OAuth troubleshooting to DEPLOYMENT_GUIDE.md
- [ ] Commit and push

---

## 🔒 Security Checklist

- ✅ JWT secret is 32+ bytes, stored in environment variable
- ✅ Cookie has `httponly=True` (prevent XSS)
- ✅ Cookie has `secure=True` in production (HTTPS only)
- ✅ Cookie has `samesite=lax` (CSRF protection)
- ✅ ID tokens verified with Google (not just trusted)
- ✅ JWT expiration validated on every `/auth/me` call
- ✅ 401 responses handled gracefully (redirect to login)
- ✅ No credentials in git repository (`.env` in `.gitignore`)

---

## 📊 Success Criteria

- ✅ Any Google user can sign in
- ✅ Each user sees only their data (tested with 2+ accounts)
- ✅ JWT tokens expire after 7 days, return 401
- ✅ Production OAuth works on Vercel with secure cookies
- ✅ No hardcoded user IDs in codebase
- ✅ Database migrations managed via Alembic

---

## 🚀 Next Steps After Phase 2

**Phase 3: Testing & CI/CD** (implement comprehensive test coverage before adding AI features)

**Future Auth Enhancements** (Phase 4+):
- Refresh token rotation (for better UX)
- GitHub OAuth (using same `/auth/login` endpoint pattern)
- Email magic links (passwordless option)
- Remember me (optional 30-day expiry)

---

## 📦 Implementation Timeline: 10-Commit Breakdown

**Branch**: `phase-2-auth`  
**Strategy**: Incremental, backwards-compatible, each commit is deployable  
**End Goal**: Squash merge to `main` with clean history

---

### Commit 1: Documentation & Design Decisions
**Branch**: `git checkout -b phase-2-auth`

**Message**: `docs: add Phase 2 OAuth plan and design decisions`

**Files**:
- ✅ `PHASE2_OAUTH_PLAN.md` (already created)
- Update `GOOGLE_OAUTH_SETUP.md` (Google Identity Services)

**Testing**:
- [ ] No code changes, zero runtime impact
- [ ] Documentation is readable and complete

**Why This Matters**: Design before code (senior engineer habit)

---

### Commit 2: Database Schema Updates
**Message**: `db: extend User model with google_id and profile fields`

**Files Modified**:
- `gymbro-api/app/models.py`

**Changes**:
```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)  # Add unique=True
    google_id: str = Field(unique=True, index=True)  # NEW
    display_name: Optional[str] = None
    picture_url: Optional[str] = None  # NEW
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
```

**Critical Rule**: Do NOT wire auth yet, do NOT remove `X-User-Id` dependency

**Testing**:
- [ ] Backend still starts: `uvicorn app.main:app --reload`
- [ ] Existing API calls still work (X-User-Id still accepted)
- [ ] No migration run yet (schema updated, DB not changed)

**Proof**: App runs exactly as before, schema is future-ready

---

### Commit 3: Alembic Migration
**Message**: `db: add alembic migration for Google OAuth fields`

**Files Created**:
- `gymbro-api/alembic.ini` (if not exists)
- `gymbro-api/alembic/env.py` (if not exists)
- `gymbro-api/alembic/versions/002_add_google_auth_fields.py`

**Files Modified**:
- `gymbro-api/requirements.txt` (add `alembic`)

**Setup Steps**:
```bash
cd gymbro-api
pip install alembic
alembic init alembic  # if not exists
alembic revision -m "add google auth fields"
# Edit the generated migration file
```

**Migration Content**:
```python
# Upgrade
op.add_column('user', sa.Column('google_id', sa.String(), nullable=True))
op.add_column('user', sa.Column('picture_url', sa.String(), nullable=True))
op.create_index(op.f('ix_user_google_id'), 'user', ['google_id'], unique=True)
op.alter_column('user', 'email', existing_type=sa.String(), unique=True)
```

**Testing**:
- [ ] Run locally: `alembic upgrade head`
- [ ] Verify rollback: `alembic downgrade -1`
- [ ] Re-apply: `alembic upgrade head`
- [ ] Check DB schema (psql or Neon console)
- [ ] App still works with existing User 1

**Proof**: Migration is reversible and doesn't break existing functionality

---

### Commit 4: JWT Utilities (Pure Logic)
**Message**: `auth: add JWT creation and verification utilities`

**Files Created**:
- `gymbro-api/app/auth_utils.py`

**Files Modified**:
- `gymbro-api/requirements.txt` (add `python-jose[cryptography]`)

**Content** (`auth_utils.py`):
```python
from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError
from fastapi import HTTPException
import os

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7

def create_jwt(user_id: int) -> str:
    """Generate JWT token with 7-day expiration"""
    expire = datetime.now(UTC) + timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {"sub": str(user_id), "exp": expire, "iat": datetime.now(UTC)}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt(token: str) -> int:
    """Validate JWT and return user_id, raise 401 if invalid/expired"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
```

**Environment Variable**:
- Add to `.env`: `JWT_SECRET_KEY=<generate with: openssl rand -hex 32>`

**Testing**:
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create test script:
```python
from app.auth_utils import create_jwt, verify_jwt
token = create_jwt(1)
print(f"Token: {token}")
user_id = verify_jwt(token)
print(f"User ID: {user_id}")
assert user_id == 1
```
- [ ] Backend still starts, no imports used yet

**Proof**: Pure utility, no side effects, easy to test

---

### Commit 5: Auth Router Skeleton
**Message**: `auth: add auth router with /me and /logout endpoints`

**Files Created**:
- `gymbro-api/app/routers/auth.py`

**Files Modified**:
- `gymbro-api/app/main.py` (include router)

**Content** (`routers/auth.py`):
```python
from fastapi import APIRouter, Cookie, HTTPException, Response, Depends
from sqlmodel import Session, select
from app.db import get_session
from app.models import User
from app.auth_utils import verify_jwt

router = APIRouter()

@router.get("/me")
def get_current_user(
    auth_token: str = Cookie(None),
    session: Session = Depends(get_session)
):
    """Get currently authenticated user (validates JWT expiry)"""
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = verify_jwt(auth_token)  # Raises 401 if expired
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "picture_url": user.picture_url
    }

@router.post("/logout")
def logout(response: Response):
    """Clear authentication cookie"""
    response.delete_cookie("auth_token")
    return {"message": "Logged out successfully"}
```

**Update** (`app/main.py`):
```python
from app.routers import auth

app.include_router(auth.router, prefix="/auth", tags=["auth"])
```

**Important**: `X-User-Id` dependency still works everywhere else

**Testing**:
- [ ] Backend starts successfully
- [ ] `GET /auth/me` returns 401 (no cookie yet)
- [ ] `POST /auth/logout` returns 200
- [ ] Existing endpoints still work with `X-User-Id` header

**Proof**: Auth infrastructure exists, doesn't break anything

---

### Commit 6: Google OAuth Flow (Backend)
**Message**: `auth: implement Google OAuth login and callback flow`

**Files Modified**:
- `gymbro-api/app/routers/auth.py` (add `/login` and `/callback`)
- `gymbro-api/requirements.txt` (add `google-auth`, `python-multipart`)

**Google Cloud Setup** (do this BEFORE coding):
- [ ] Create Google Cloud project
- [ ] Enable Google Identity Services API
- [ ] Configure OAuth consent screen
- [ ] Create OAuth credentials
- [ ] Add redirect URIs (localhost + production)
- [ ] Store credentials in `.env`:
  ```bash
  GOOGLE_CLIENT_ID=...
  GOOGLE_CLIENT_SECRET=...
  FRONTEND_URL=http://localhost:5173
  ```

**Add to** (`routers/auth.py`):
```python
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
from urllib.parse import urlencode

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")

@router.get("/login")
def google_login():
    """Redirect to Google OAuth consent screen"""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{FRONTEND_URL}/auth/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return {"url": google_auth_url}

@router.get("/callback")
def google_callback(
    code: str,
    session: Session = Depends(get_session),
    response: Response = None
):
    """Handle OAuth callback, create/fetch user, set JWT cookie"""
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": f"{FRONTEND_URL}/auth/callback",
        "grant_type": "authorization_code"
    }
    
    token_response = requests.post(token_url, data=token_data).json()
    id_token_str = token_response.get("id_token")
    
    # Verify ID token
    idinfo = id_token.verify_oauth2_token(
        id_token_str, 
        google_requests.Request(), 
        GOOGLE_CLIENT_ID
    )
    
    # Extract user info
    google_id = idinfo["sub"]
    email = idinfo["email"]
    display_name = idinfo.get("name")
    picture_url = idinfo.get("picture")
    
    # Upsert user
    user = session.exec(select(User).where(User.google_id == google_id)).first()
    if not user:
        user = User(
            google_id=google_id,
            email=email,
            display_name=display_name,
            picture_url=picture_url
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    
    # Generate JWT and set cookie
    token = create_jwt(user.id)
    is_production = "vercel.app" in FRONTEND_URL
    
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    
    # Redirect to frontend
    return {"redirect_url": FRONTEND_URL}
```

**Testing**:
- [ ] Start backend with env vars set
- [ ] Visit `http://localhost:8000/api/auth/login` in browser
- [ ] Redirects to Google login
- [ ] Sign in with Google account
- [ ] Callback creates User in database
- [ ] Cookie is set (check DevTools → Application → Cookies)
- [ ] `/auth/me` now returns user data

**Proof**: Can authenticate via Google, user created, JWT works

---

### Commit 7: Frontend Auth Context
**Message**: `frontend: add auth context and login state management`

**Files Created**:
- `gymbro-web/src/contexts/AuthContext.tsx`
- `gymbro-web/src/pages/LoginPage.tsx`

**Content** (`AuthContext.tsx`):
```typescript
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

type User = {
  id: number
  email: string
  display_name: string | null
  picture_url: string | null
}

type AuthContextType = {
  user: User | null
  isLoading: boolean
  login: () => void
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const res = await fetch('/api/auth/me', { credentials: 'include' })
      if (res.ok) {
        const userData = await res.json()
        setUser(userData)
      }
    } catch (error) {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  const login = () => {
    window.location.href = '/api/auth/login'
  }

  const logout = async () => {
    await fetch('/api/auth/logout', { 
      method: 'POST', 
      credentials: 'include' 
    })
    setUser(null)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
```

**Content** (`LoginPage.tsx`):
```typescript
import { useAuth } from '../contexts/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Gym Bro</h1>
          <p className="text-gray-600">Track your fitness journey</p>
        </div>
        <button
          onClick={login}
          className="w-full flex items-center justify-center gap-3 bg-white border-2 border-gray-300 rounded-lg px-6 py-3 hover:bg-gray-50 transition"
        >
          <img 
            src="https://www.google.com/favicon.ico" 
            alt="Google" 
            className="w-5 h-5" 
          />
          <span className="font-medium">Sign in with Google</span>
        </button>
      </div>
    </div>
  )
}
```

**Files Modified**:
- `gymbro-web/src/main.tsx` (wrap App in AuthProvider)

**Testing**:
- [ ] Frontend compiles successfully
- [ ] Can import and render LoginPage
- [ ] Click "Sign in with Google" triggers redirect
- [ ] Auth context provides user state
- [ ] **Do not protect routes yet** (still accessible without auth)

**Proof**: Auth UI exists, state management works, doesn't break existing flows

---

### Commit 8: Switch API Client to Cookie Auth
**Message**: `frontend: switch API client from X-User-Id to cookie auth`

**Files Modified**:
- `gymbro-web/src/lib/api.ts`

**Changes**:
```typescript
// Remove these lines:
// const USER_ID = import.meta.env.VITE_USER_ID ?? '1'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include',  // NEW: Send cookies
    headers: {
      'Content-Type': 'application/json',
      // REMOVED: 'X-User-Id': USER_ID,
      ...(options.headers || {}),
    },
  })

  // NEW: Handle 401 redirects
  if (res.status === 401) {
    window.location.href = '/login'
    throw new Error('Authentication required')
  }

  if (!res.ok) {
    const message = await res.text()
    throw new Error(message || `Request failed (${res.status})`)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}
```

**Backend Change** (update `deps.py` to support cookies):
```python
from fastapi import Cookie, Header, HTTPException, status
from app.auth_utils import verify_jwt

def get_user_id(
    auth_token: str = Cookie(None),
    x_user_id: int = Header(None, alias="X-User-Id")  # Temporary backward compat
) -> int:
    """Extract user_id from JWT cookie (or legacy header temporarily)"""
    if auth_token:
        return verify_jwt(auth_token)
    
    # Fallback for testing (remove in Commit 10)
    if x_user_id and x_user_id > 0:
        return x_user_id
    
    raise HTTPException(status_code=401, detail="Not authenticated")
```

**Testing**:
- [ ] Sign in via Google OAuth
- [ ] Create check-in, meal, workout
- [ ] Verify data persists
- [ ] Open DevTools → Network → check cookies are sent
- [ ] Sign out, verify 401 on API calls
- [ ] Sign in again, verify data loads

**Proof**: Cookie-based auth works end-to-end, data is user-scoped

---

### Commit 9: Protect Routes
**Message**: `frontend: protect routes behind authentication`

**Files Modified**:
- `gymbro-web/src/App.tsx`

**Changes**:
```typescript
import { useAuth } from './contexts/AuthContext'
import LoginPage from './pages/LoginPage'

function App() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    )
  }

  if (!user) {
    return <LoginPage />
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<TodayPage />} />
        <Route path="/meals" element={<MealsPage />} />
        <Route path="/workout" element={<WorkoutPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Routes>
      <BottomNav />
    </BrowserRouter>
  )
}
```

**Update ProfilePage** (show user info + logout):
```typescript
import { useAuth } from '../contexts/AuthContext'

export default function ProfilePage() {
  const { user, logout } = useAuth()

  return (
    <div className="p-4">
      <div className="flex items-center gap-4 mb-6">
        {user?.picture_url && (
          <img 
            src={user.picture_url} 
            alt={user.display_name || 'User'} 
            className="w-16 h-16 rounded-full"
          />
        )}
        <div>
          <h2 className="text-xl font-bold">{user?.display_name}</h2>
          <p className="text-gray-600">{user?.email}</p>
        </div>
      </div>
      <button
        onClick={logout}
        className="w-full bg-red-500 text-white py-2 rounded-lg hover:bg-red-600"
      >
        Sign Out
      </button>
    </div>
  )
}
```

**Testing**:
- [ ] Visit app without auth → redirected to login
- [ ] Sign in → see app
- [ ] Create data as User A
- [ ] Sign out
- [ ] Sign in as User B (different Google account)
- [ ] Verify User B sees ZERO data from User A
- [ ] Create data as User B
- [ ] Sign back in as User A → see only User A's data

**Proof**: Multi-user isolation works, no data leaks

---

### Commit 10: Cleanup
**Message**: `cleanup: remove temporary auth and legacy headers`

**Files Modified**:
- `gymbro-api/app/deps.py` (remove `X-User-Id` fallback)
- `gymbro-web/src/lib/api.ts` (remove any TODOs)
- `README.md` (document OAuth setup)
- `DEPLOYMENT_GUIDE.md` (add OAuth troubleshooting)

**Remove from** (`deps.py`):
```python
def get_user_id(auth_token: str = Cookie(None)) -> int:
    """Extract user_id from JWT cookie"""
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return verify_jwt(auth_token)
```

**Update** `README.md`:
```markdown
## Authentication

This app uses Google OAuth 2.0 for authentication.

**Setup**:
1. Create Google Cloud project
2. Enable Google Identity Services API
3. Create OAuth credentials
4. Add environment variables:
   ```bash
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   JWT_SECRET_KEY=<openssl rand -hex 32>
   FRONTEND_URL=http://localhost:5173
   ```

**Multi-user support**: Each user sees only their own data.
```

**Testing**:
- [ ] Remove `.env` file temporarily
- [ ] Verify app fails gracefully with clear error message
- [ ] Restore `.env`
- [ ] Full smoke test: sign in → CRUD operations → sign out
- [ ] Deploy to Vercel (update env vars)
- [ ] Test production OAuth flow

**Proof**: No legacy code remains, documentation is complete

---

## 🚀 Branch Workflow

```bash
# Start
git checkout -b phase-2-auth

# Make all 10 commits (one at a time, test after each)
git add <files>
git commit -m "<message>"

# When done, merge to main
git checkout main
git pull origin main

# Option A: Squash merge (clean history)
git merge --squash phase-2-auth
git commit -m "feat: add Google OAuth authentication (Phase 2)"
git push origin main

# Option B: Normal merge (preserve commit history)
git merge phase-2-auth --no-ff
git push origin main

# Cleanup
git branch -d phase-2-auth
```

---

## ✅ Success Checklist

After all 10 commits:
- [ ] Any Google user can sign in
- [ ] JWT tokens work with 7-day expiration
- [ ] Cookies are secure (httpOnly, secure in prod, samesite=lax)
- [ ] Multi-user data isolation verified
- [ ] Production OAuth works on Vercel
- [ ] No hardcoded user IDs in codebase
- [ ] Alembic manages all migrations
- [ ] Documentation updated
- [ ] Zero TODOs related to auth

---

**Ready to start implementation?**
