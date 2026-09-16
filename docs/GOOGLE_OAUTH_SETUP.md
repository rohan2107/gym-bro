# Google OAuth 2.0 Setup Guide

**Goal**: Implement "Sign in with Google" for multi-user authentication  
**Time**: 2–3 hours for full setup  
**Difficulty**: Medium (new concepts, but well-documented)

---

## 🎯 What We're Building

```
User clicks "Sign in with Google"
    ↓
Redirected to Google login page
    ↓
User approves app access to email + profile
    ↓
Redirected back to app with auth code
    ↓
Backend exchanges code for ID token
    ↓
Backend creates/fetches User in database
    ↓
Backend returns JWT token (httpOnly, Secure, SameSite cookie)
    ↓
Frontend sends cookie automatically with all API calls
    ↓
User can log in/out, see their data only
```

---

## Part 1: Google Cloud Project Setup

### Step 1.1: Create Google Cloud Project
1. Go to https://console.cloud.google.com
2. Click project selector (top-left) → "New Project"
3. Name: `Gym Bro`
4. Organization: Leave blank
5. Click "Create"

**Wait for project to be created (~1 minute)**

### Step 1.2: Enable Google Identity Services
1. In Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google Identity Services"
3. Click "Google Identity Services API" → "Enable"

**Note**: We're using OAuth 2.0 / OpenID Connect (modern standard), NOT the deprecated Google+ API

**Wait for API to be enabled**

### Step 1.3: Create OAuth 2.0 Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth Client ID"
3. If prompted, "Configure OAuth Consent Screen" first:
   - **User type**: External
   - **App name**: Gym Bro
   - **User support email**: Your email
   - **Scopes**: Add `email`, `profile` (default scopes)
   - Save → Continue
4. Back to creating credentials:
   - **Application type**: Web application
   - **Name**: Gym Bro Web Client
   - **Authorized redirect URIs**: Add:
     - `http://localhost:5173/auth/callback` (dev)
     - `http://localhost:3000/auth/callback` (alternative dev)
     - `https://yourusername.vercel.app/auth/callback` (production)
       - Replace `yourusername` with your Vercel subdomain
5. Click "Create"

### Step 1.4: Copy Credentials
Dialog shows your credentials:
- **Client ID**: `xxx...apps.googleusercontent.com`
- **Client Secret**: `xxx...`

**Save these securely!** (They're like passwords)

---

## Part 2: Backend Setup (FastAPI + OAuth)

### Step 2.1: Install Dependencies
```bash
cd gymbro-api
pip install google-auth-oauthlib google-auth-httplib2 python-jose[cryptography]
pip freeze > requirements.txt
```

### Step 2.2: Create Auth Router
Create file: `gymbro-api/app/routers/auth.py`

```python
"""Google OAuth 2.0 authentication."""
from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel
from sqlmodel import Session, select
from jose import JWTError, jwt

from ..db import get_session
from ..models import User
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Security
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to .env
ALGORITHM = "HS256"

class GoogleTokenRequest(BaseModel):
    """Frontend sends Google ID token."""
    token: str

class UserResponse(BaseModel):
    """User data returned after login."""
    id: int
    email: str
    display_name: Optional[str] = None
    jwt_token: str

@router.post("/google/callback", response_model=UserResponse)
def google_callback(
    request: GoogleTokenRequest,
    session: Session = Depends(get_session),
):
    """
    Exchange Google ID token for JWT.
    
    Frontend flow:
    1. User clicks "Sign in with Google"
    2. Google returns ID token
    3. Frontend sends token to this endpoint
    4. Backend verifies token with Google, creates User, returns JWT
    """
    try:
        # Verify token with Google (never trust frontend!)
        id_info = id_token.verify_oauth2_token(
            request.token,
            google_requests.Request(),
            "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"  # TODO: Use settings
        )
        
        # Check token is for our app
        if id_info['aud'] != "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com":
            raise ValueError("Token audience mismatch")
        
        # Extract user info from Google token
        google_sub = id_info['sub']  # Unique Google ID
        email = id_info['email']
        display_name = id_info.get('name', email.split('@')[0])
        
        # Find or create User in database
        user = session.exec(
            select(User).where(User.email == email)
        ).first()
        
        if not user:
            # New user → create
            user = User(
                email=email,
                display_name=display_name,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        
        # Generate JWT token
        jwt_token = create_jwt_token(user.id, user.email)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            jwt_token=jwt_token
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

def create_jwt_token(user_id: int, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT token for user."""
    if expires_delta is None:
        expires_delta = timedelta(days=7)
    
    expire = datetime.now(UTC) + expires_delta
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/logout")
def logout():
    """Logout endpoint (mainly frontend clears token)."""
    return {"message": "Logged out"}

@router.get("/me")
def get_current_user(
    token: str = Depends(get_bearer_token),
    session: Session = Depends(get_session),
):
    """Get current logged-in user."""
    user_id = verify_jwt_token(token)
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_bearer_token(authorization: str = None) -> str:
    """Extract JWT token from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    return parts[1]

def verify_jwt_token(token: str) -> int:
    """Verify JWT and return user_id."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Step 2.3: Update Main App
Add auth router to `gymbro-api/app/main.py`:

```python
from .routers import health, food_logs, daily_checkins, weight_entries, workouts, exercise_sets, auth

def create_app() -> FastAPI:
    app = FastAPI(...)
    
    # Include routers
    app.include_router(auth.router)  # Add this
    app.include_router(health.router)
    # ... other routers
    
    return app
```

### Step 2.4: Update Dependencies
Update `gymbro-api/app/deps.py` to use JWT instead of header:

```python
from fastapi import Header, HTTPException, status, Depends
from jose import jwt, JWTError
from typing import Optional

SECRET_KEY = "your-secret-key"  # TODO: Move to .env
ALGORITHM = "HS256"

def get_user_id(authorization: Optional[str] = Header(None)) -> int:
    """Extract user_id from JWT token in Authorization header."""
    if not authorization:
        # Fallback to X-User-Id header for development
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except (ValueError, JWTError):
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Step 2.5: Add Configuration
Update `gymbro-api/app/config.py`:

```python
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    """Application settings."""
    
    DATABASE_URL: str = "sqlite:///./gymbro.db"
    GOOGLE_CLIENT_ID: str  # Required in production
    GOOGLE_CLIENT_SECRET: str  # Required in production
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()
```

### Step 2.6: Update .env
Add to `gymbro-api/.env`:

```
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
JWT_SECRET_KEY=your-long-secret-key-min-32-chars
```

---

## Part 3: Frontend Setup (React)

### Step 3.1: Install Google OAuth Library
```bash
cd gymbro-web
npm install @react-oauth/google
```

### Step 3.2: Create Auth Context
Create file: `gymbro-web/src/contexts/AuthContext.tsx`

```tsx
import { createContext, useState, useEffect, ReactNode } from 'react'

export type User = {
  id: number
  email: string
  display_name?: string
}

export type AuthContextType = {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (googleToken: string) => Promise<void>
  logout: () => void
  isLoggedIn: boolean
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check if user is already logged in (on page load)
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token')
    if (storedToken) {
      setToken(storedToken)
      // Optional: verify token is still valid
    }
    setIsLoading(false)
  }, [])

  const login = async (googleToken: string) => {
    try {
      // Send Google token to backend
      const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/google/callback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: googleToken }),
      })

      if (!response.ok) throw new Error('Login failed')

      const data = await response.json()
      
      // Store JWT token
      localStorage.setItem('auth_token', data.jwt_token)
      setToken(data.jwt_token)
      setUser({
        id: data.id,
        email: data.email,
        display_name: data.display_name,
      })
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        isLoggedIn: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useAuth()
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
```

### Step 3.3: Create Login Page
Create file: `gymbro-web/src/pages/Login.tsx`

```tsx
import { useContext } from 'react'
import { useNavigate } from 'react-router-dom'
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google'
import { AuthContext } from '../contexts/AuthContext'

export function LoginPage() {
  const navigate = useNavigate()
  const authContext = useContext(AuthContext)

  if (!authContext) throw new Error('AuthContext not found')
  const { login } = authContext

  const handleGoogleLogin = async (credentialResponse: any) => {
    try {
      await login(credentialResponse.credential)
      navigate('/') // Redirect to main app
    } catch (error) {
      alert('Login failed. Please try again.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-600 to-purple-600">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
        <h1 className="text-3xl font-bold text-center mb-2">Gym Bro</h1>
        <p className="text-gray-600 text-center mb-8">Track your fitness journey</p>

        <GoogleOAuthProvider clientId="YOUR_GOOGLE_CLIENT_ID">
          <div className="flex justify-center">
            <GoogleLogin
              onSuccess={handleGoogleLogin}
              onError={() => console.log('Login failed')}
              theme="outline"
              size="large"
            />
          </div>
        </GoogleOAuthProvider>

        <p className="text-xs text-gray-500 text-center mt-6">
          Sign in with your Google account to get started
        </p>
      </div>
    </div>
  )
}
```

### Step 3.4: Protect Routes
Update `gymbro-web/src/App.tsx`:

```tsx
import { useContext } from 'react'
import { AuthContext } from './contexts/AuthContext'
import { LoginPage } from './pages/Login'
import { MainApp } from './MainApp'

export function App() {
  const authContext = useContext(AuthContext)

  if (!authContext) throw new Error('AuthContext not found')
  const { isLoading, isLoggedIn } = authContext

  if (isLoading) return <div>Loading...</div>

  if (!isLoggedIn) return <LoginPage />

  return <MainApp />
}
```

### Step 3.5: Add User Profile Card
Update `gymbro-web/src/MainApp.tsx`:

```tsx
import { useContext } from 'react'
import { AuthContext } from './contexts/AuthContext'

export function MainApp() {
  const authContext = useContext(AuthContext)
  
  if (!authContext) throw new Error('AuthContext not found')
  const { user, logout } = authContext

  return (
    <div>
      {/* Header with user profile */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Gym Bro</h1>
            <p className="text-sm text-gray-600">Hey, {user?.display_name || user?.email}!</p>
          </div>
          <button
            onClick={logout}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Rest of app */}
      {/* ... */}
    </div>
  )
}
```

### Step 3.6: Update API Client
Update `gymbro-web/src/lib/api.ts`:

```typescript
export const api = {
  // All existing endpoints...
  
  // Update: Include JWT token from localStorage
  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const token = localStorage.getItem('auth_token')
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...(options.headers || {}),
      },
    })
    
    if (!res.ok) {
      if (res.status === 401) {
        // Token expired → redirect to login
        localStorage.removeItem('auth_token')
        window.location.href = '/login'
      }
      throw new Error(`Request failed (${res.status})`)
    }
    
    if (res.status === 204) return undefined as T
    return (await res.json()) as T
  }
}
```

---

## Part 4: Environment Configuration

### Backend (.env)
```
DATABASE_URL=postgresql://...
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
JWT_SECRET_KEY=your-long-random-secret-key-at-least-32-chars
```

### Frontend (.env.local)
```
VITE_API_URL=http://localhost:8000/api
VITE_GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
```

### Vercel (Production)
1. Frontend project → Settings → Environment Variables
   - Add: `VITE_GOOGLE_CLIENT_ID` = your client ID
   - Add: `VITE_API_URL` = your backend URL

2. Backend project → Settings → Environment Variables
   - Add: `GOOGLE_CLIENT_ID`
   - Add: `GOOGLE_CLIENT_SECRET`
   - Add: `JWT_SECRET_KEY` (use strong random key)

---

## Part 5: Testing

### Test Locally
```bash
# Terminal 1: Backend
cd gymbro-api
.venv\Scripts\activate
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd gymbro-web
npm run dev

# Go to http://localhost:5173
# Click "Sign in with Google"
# Log in with your Google account
# Should redirect to main app
# Check localStorage → should have auth_token
```

### Test API Authorization
```bash
# Get your JWT token (check browser localStorage)
TOKEN="your-jwt-token-here"

# Try API request with token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/food-logs/

# Should return your food logs (empty on first login)
```

---

## 🚨 Security Checklist

- [ ] `JWT_SECRET_KEY` is at least 32 characters, random
- [ ] `GOOGLE_CLIENT_SECRET` never exposed in frontend code
- [ ] JWT token stored in httpOnly cookie (more secure than localStorage)
- [ ] CORS configured to allow only your frontend domain
- [ ] All API endpoints require valid JWT (except /auth/google/callback)
- [ ] Token expiration set (7 days is reasonable)
- [ ] User isolation verified (user can only see their own data)

---

## Troubleshooting

### "Invalid CLIENT_ID"
- Check `VITE_GOOGLE_CLIENT_ID` matches your Google Console project
- Ensure redirect URI is registered in Google Console

### "Token verification failed"
- Verify `GOOGLE_CLIENT_ID` in backend matches Google Console
- Check token hasn't expired
- Ensure `GOOGLE_CLIENT_SECRET` is correct

### "Unauthorized error on API calls"
- Check JWT token is in localStorage
- Verify Authorization header format: `Bearer <token>`
- Check token hasn't expired (7 days)

### "User data not saved"
- Verify backend database has User table (check migrations ran)
- Check database connection is working

---

## Next Steps

1. **This week**: Complete OAuth setup + test locally
2. **Next week**: Deploy to Vercel (both frontend + backend)
3. **Then**: Mobile UI improvements
4. **Then**: AI meal photos (Phase 3)

---

## Resources

- Google OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- PyJWT: https://pyjwt.readthedocs.io/
- @react-oauth/google: https://www.npmjs.com/package/@react-oauth/google
