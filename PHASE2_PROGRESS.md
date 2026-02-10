# Phase 2: OAuth Setup Progress

## ✅ Completed (Backend Foundation)

### 1. Database Schema Updates
- [x] Updated User model with `google_id` and `picture_url` fields
- [x] Made `email` unique
- [x] Added proper indexing

### 2. Dependencies Added
- [x] `python-jose[cryptography]` - JWT token creation/validation
- [x] `google-auth` - Google ID token verification
- [x] `python-multipart` - OAuth form handling
- [x] `alembic` - Database migrations

### 3. Authentication Infrastructure
- [x] Created `auth_utils.py` with JWT utilities
  - `create_jwt()` - Generate 7-day tokens
  - `verify_jwt()` - Validate and extract user_id
- [x] Created `auth.py` router with endpoints:
  - `GET /auth/me` - Get current user
  - `POST /auth/logout` - Clear auth cookie
  - `GET /auth/google/login` - Initiate OAuth flow
  - `GET /auth/google/callback` - Handle OAuth response
- [x] Updated `deps.py` to support both JWT cookies and legacy X-User-Id header
- [x] Added auth router to main.py

## 📋 Next Steps

### 4. Install Dependencies & Setup Google OAuth
```powershell
# Install new dependencies
cd gymbro-api
pip install -r requirements.txt

# Generate JWT secret
# Run in PowerShell:
$secret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
echo "JWT_SECRET_KEY=$secret"

# Create .env file (copy from .env.example and fill in values)
cp .env.example .env
```

### 5. Google Cloud Setup
1. Go to https://console.cloud.google.com
2. Create new project: "Gym Bro"
3. Enable "Google Identity Services API"
4. Configure OAuth consent screen:
   - User Type: External
   - App name: "Gym Bro"
   - Scopes: openid, email, profile
5. Create OAuth credentials:
   - Application type: Web application
   - Authorized redirect URIs:
     - http://localhost:5173/auth/callback
     - https://your-app.vercel.app/auth/callback
6. Copy Client ID and Client Secret to `.env`

### 6. Database Migration (Alembic)
```powershell
cd gymbro-api

# Initialize Alembic (if not exists)
alembic init alembic

# Configure alembic.ini with your DATABASE_URL

# Create migration
alembic revision -m "add google oauth fields"

# Edit the generated migration file to add:
# - google_id column (unique, indexed)
# - picture_url column
# - Make email unique

# Apply migration
alembic upgrade head
```

### 7. Test Backend
```powershell
# Start backend
uvicorn app.main:app --reload

# Test endpoints:
# http://localhost:8000/docs
# Try /auth/google/login
# Should redirect to Google
```

### 8. Frontend Implementation
- [ ] Create AuthContext
- [ ] Create LoginPage
- [ ] Update API client to use cookies
- [ ] Protect routes
- [ ] Update ProfilePage with logout

## 🎯 Status
**Current**: Backend infrastructure complete  
**Next**: Install dependencies and configure Google OAuth  
**Blocker**: Need Google Cloud credentials

## 📝 Notes
- Backward compatible: X-User-Id header still works
- JWT tokens expire after 7 days
- Cookies are httpOnly and secure in production
- User info updates on each login (email, name, picture)
