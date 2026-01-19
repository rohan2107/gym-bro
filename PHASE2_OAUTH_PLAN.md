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

**Ready to start implementation?**
