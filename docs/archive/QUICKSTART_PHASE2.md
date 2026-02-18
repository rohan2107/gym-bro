# Phase 2 Quick Start Guide

## 🎉 What We Just Built

You now have a complete OAuth authentication backend! Here's what's ready:

### Backend Infrastructure ✅
1. **User Model**: Extended with `google_id`, `picture_url`
2. **JWT Utilities**: Token creation & validation (7-day expiry)
3. **Auth Router**: 4 endpoints for OAuth flow
4. **Backward Compatible**: Still works with `X-User-Id` header

### API Endpoints Ready:
- `GET /api/auth/google/login` - Start OAuth flow
- `GET /api/auth/google/callback` - Handle Google response
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Sign out

## 🚀 Next: Install & Configure

### Step 1: Install Dependencies (2 minutes)
```powershell
cd gymbro-api
pip install -r requirements.txt
```

### Step 2: Generate JWT Secret (30 seconds)
```powershell
# PowerShell - generates random 64-char hex string
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

### Step 3: Create `.env` file
Create `gymbro-api/.env`:
```env
DATABASE_URL=postgresql://your_neon_connection_string
JWT_SECRET_KEY=paste_generated_secret_here
FRONTEND_URL=http://localhost:5173

# Leave these empty for now - we'll add after Google Cloud setup
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

### Step 4: Google Cloud Setup (10 minutes)
**Follow**: [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md)

Quick version:
1. Visit https://console.cloud.google.com
2. Create project "Gym Bro"
3. Enable "Google Identity Services API"  
4. OAuth consent screen → External → Add scopes: openid, email, profile
5. Credentials → Create OAuth Client ID → Web application
6. Add redirect URIs:
   - `http://localhost:5173/auth/callback`
   - `https://your-vercel-app.vercel.app/auth/callback`
7. Copy Client ID & Secret to `.env`

### Step 5: Update Database (5 minutes)
```powershell
cd gymbro-api

# Initialize Alembic
alembic init alembic

# Edit alembic.ini - set sqlalchemy.url to your DATABASE_URL

# Create migration
alembic revision -m "add google oauth fields to user"
```

Edit the generated migration file (in `alembic/versions/`):
```python
def upgrade():
    op.add_column('user', sa.Column('google_id', sa.String(), nullable=True))
    op.add_column('user', sa.Column('picture_url', sa.String(), nullable=True))
    op.create_index(op.f('ix_user_google_id'), 'user', ['google_id'], unique=True)
    op.alter_column('user', 'email', existing_type=sa.String(), unique=True)

def downgrade():
    op.drop_index(op.f('ix_user_google_id'), table_name='user')
    op.drop_column('user', 'picture_url')
    op.drop_column('user', 'google_id')
```

Apply migration:
```powershell
alembic upgrade head
```

### Step 6: Test Backend (2 minutes)
```powershell
uvicorn app.main:app --reload
```

Visit: http://localhost:8000/docs

Try:
1. `GET /auth/google/login` - Should return a Google OAuth URL
2. Click the URL in response - Should redirect to Google login

## 🎯 Current Status

**✅ Working Now:**
- All existing endpoints still work with `X-User-Id` header
- Auth endpoints are live
- Database schema is ready (after migration)

**⏳ Not Working Yet:**
- Google OAuth (needs credentials)
- Frontend login UI (Phase 2B - coming next)

## 📦 What's Next?

After you:
1. Install dependencies
2. Set up Google Cloud
3. Run database migration

Then we'll build:
1. **Frontend AuthContext** - React auth state management
2. **LoginPage** - Google sign-in button
3. **Protected Routes** - Redirect unauthenticated users
4. **Update API Client** - Use cookies instead of X-User-Id

## ⏱️ Time Estimate

- **Google Cloud setup**: 10-15 minutes (one-time)
- **Alembic migration**: 5 minutes (one-time)
- **Frontend implementation**: 1-2 hours (next session)

## 💡 Tips

- Keep GitHub Copilot handy for Alembic migration code
- Save your Google Client ID/Secret somewhere safe
- The JWT secret should be truly random
- Test OAuth in incognito window to avoid account conflicts

## 🆘 If You Get Stuck

Common issues:
1. **Import errors**: Run `pip install -r requirements.txt`
2. **JWT errors**: Check `JWT_SECRET_KEY` is set in `.env`
3. **Google redirect fails**: Check redirect URIs match exactly
4. **Database errors**: Make sure Alembic migration ran successfully

## 📖 Reference

- [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md) - Detailed Google Cloud guide
- [PHASE2_OAUTH_PLAN.md](PHASE2_OAUTH_PLAN.md) - Full implementation plan
- [PHASE2_PROGRESS.md](PHASE2_PROGRESS.md) - Current progress tracker

---

**Ready to install dependencies?** Run:
```powershell
cd gymbro-api
pip install -r requirements.txt
```
