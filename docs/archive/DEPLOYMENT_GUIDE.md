# Deployment Guide: Vercel + Neon PostgreSQL

**Status**: ✅ Production deployment complete (January 19, 2026)  
**Live URL**: https://gym-bro-chi.vercel.app/  
**Cost**: $0 (Vercel + Neon free tiers)  

This guide documents the actual deployment process used for Gym Bro on Vercel.

---

## Prerequisites

- GitHub account (required for Vercel)
- Vercel account (linked to GitHub)
- Neon account (PostgreSQL database)

---

## Part 1: Database Setup (Neon PostgreSQL)

### Step 1.1: Create Neon Account
1. Go to https://neon.tech
2. Click "Sign Up" → "Continue with GitHub"
3. Authorize Neon to access your GitHub
4. Create organization name (e.g., "gymbro")
5. Confirm email

### Step 1.2: Create Database
1. Click "Create project"
2. Name: `gym-bro-prod`
3. Database name: `gymbro` (leave default)
4. Region: Pick closest to you (e.g., us-east-1)
5. Click "Create"

**You now have a PostgreSQL database!**

### Step 1.3: Get Connection String
1. In Neon dashboard, click your project
2. Go to "Connection string" tab
3. Select "Python" (fastapi-compatible)
4. Copy the connection string (looks like):
   ```
   postgresql://user:password@host/db?sslmode=require
   ```
5. **Save this securely** (you'll need it for Vercel)

### Step 1.4: Run Migrations Locally
Before deploying, verify schema works on Postgres:

```powershell
# Update local .env to test Postgres
Set-Content -Path "gymbro-api/.env" -Value "DATABASE_URL=postgresql://user:password@host/db?sslmode=require"

# Start backend (will auto-create tables)
python -m uvicorn app.main:app --reload

# Verify tables created
# Visit http://localhost:8000/health (should return {"status": "ok"})
```

**✅ If no errors, schema is Postgres-compatible!**

---

## Part 2: Vercel Frontend Deployment

### Step 2.1: Prepare Repository
Ensure your repo has these files:
- `vercel.json` (routing configuration)
- `gymbro-web/package.json` (dependencies)
- `gymbro-web/vite.config.ts` (build config)

### Step 2.2: Deploy Frontend
1. Go to https://vercel.com/dashboard
2. Click "Add New" → "Project"
3. Import your `gym-bro` repository
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `gymbro-web` (not needed if using vercel.json)
   - **Build Command**: Auto-detected (npm run build)
   - **Output Directory**: `dist`
   - **Install Command**: Auto-detected (npm ci)

5. Click "Deploy"

### Step 2.3: Set Frontend Environment Variables
After first deployment:
1. Go to Project Settings → Environment Variables
2. Add (optional for MVP):
   ```
   VITE_USER_ID=1
   ```
3. Click "Save"

**✅ Frontend should now be live!**

---

## Part 3: Vercel Backend Deployment

### Step 3.1: Prepare Backend Files

Key files required:
- `api/handler.py` - Serverless function handler (imports FastAPI app directly, no adapters)
- `api/requirements.txt` - Python dependencies (FastAPI, SQLModel, psycopg2-binary, Pydantic)
- `gymbro-api/app/main.py` - Must include `root_path="/api"` for Vercel routing

**Critical Configuration**: 
In your FastAPI app factory, set `root_path="/api"` so Vercel routing works correctly:
```python
app = FastAPI(..., root_path="/api")
```

### Step 3.2: Configure Vercel Routing

Your `vercel.json` at repo root:
```json
{
  "version": 2,
  "buildCommand": "cd gymbro-web && npm ci && npm run build",
  "outputDirectory": "gymbro-web/dist",
  "routes": [
    { "src": "/api/(.*)", "dest": "/api/handler" },
    { "handle": "filesystem" },
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

### Step 3.3: Set Backend Environment Variables

**Critical**: Add DATABASE_URL before deploying!

1. Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add:
   - **Key**: `DATABASE_URL`
   - **Value**: Your Neon connection string from Part 1
   - **Environment**: Production (and Preview if needed)
3. Save

### Step 3.4: Deploy

Backend deploys automatically with frontend (single Vercel project). After deployment:
- Vercel installs Python dependencies from `api/requirements.txt`
- Creates serverless function at `/api/handler`
- Routes `/api/*` requests to the function

### Step 3.5: Verify

Test health endpoint: `https://your-app.vercel.app/api/health`  
Expected: `{"status":"ok"}`

**Troubleshooting**:
- **404**: Check `root_path="/api"` in main.py
- **500**: Verify DATABASE_URL is set correctly
- **Import errors**: Check api/requirements.txt

---

## Part 4: Testing & Validation

### Quick Verification

1. **Health check**: `https://your-app.vercel.app/api/health` → `{"status":"ok"}`
2. **Frontend**: `https://your-app.vercel.app/` → Gym Bro UI loads
3. **Full flow**: Create check-in, meal, workout via UI → data persists on refresh

### View Logs

Vercel Dashboard → Deployment → Functions → `/api/handler` → View logs for errors

---

## Part 5: Ongoing Maintenance

### Automatic Deployment
Vercel auto-deploys on every push to `main` branch in GitHub.

### Database Backups  
Neon provides automatic daily backups (free tier: 7-day retention).

### Monitoring
- **Analytics**: Vercel Dashboard → Project → Analytics
- **Function Logs**: Deployment → Functions → Logs
- **Error Tracking**: Filter logs by "error"

---

## Troubleshooting

### Database Connection Failed
- Check `DATABASE_URL` is set in Vercel environment variables
- Verify Neon database is active in dashboard
- Ensure connection string format is correct (includes `?sslmode=require`)

### 404 on API Routes
- Verify `root_path="/api"` is set in FastAPI app
- Check `vercel.json` routing configuration

### CORS Errors
- Ensure CORSMiddleware is configured in backend
- Verify frontend URL is in `allow_origins` list

### Cold Start Latency
- First request takes 1-5 seconds (normal for serverless functions)
- Function stays warm for ~15 minutes after first call
- Acceptable trade-off for free tier

---

## Cost Summary

| Service | Free Tier | Cost |
|---------|-----------|------|
| Neon PostgreSQL | 3 GB storage, 3 projects | $0 |
| Vercel | 100K function invocations/month | $0 |
| **Total** | | **$0/month** |

---

## Next Steps

Phase 2: Implement Google OAuth 2.0 authentication. See [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md) for details.
