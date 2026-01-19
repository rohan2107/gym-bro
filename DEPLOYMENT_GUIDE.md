# Deployment Guide: Vercel + Neon PostgreSQL

**Status**: ✅ Production deployment complete (January 19, 2026)  
**Live URL**: https://gym-62nyxe7vc-rohan-anthonys-projects-a86489a8.vercel.app  
**Cost**: $0 (Vercel + Neon free tiers)  

This guide documents the actual deployment process used for Gym Bro on Vercel.

---

## 📋 Prerequisites

- ✅ GitHub account (required for Vercel)
- ✅ Vercel account (linked to GitHub)
- ✅ Neon account (PostgreSQL database)
- Optional: Custom domain (for production URL)

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

Your repository should have:
- `api/handler.py` - Serverless function handler
- `api/requirements.txt` - Python dependencies
- `gymbro-api/app/` - FastAPI application code

#### `api/handler.py` (Serverless Entry Point)
```python
"""Vercel serverless handler for FastAPI app."""
import sys
from pathlib import Path

# Add gymbro-api to Python path
repo_root = Path(__file__).parent.parent
gymbro_api_path = repo_root / "gymbro-api"
sys.path.insert(0, str(gymbro_api_path))

# Import FastAPI app - Vercel supports it natively
from app.main import app

# Vercel uses the 'app' variable directly (no adapter needed)
```

#### `api/requirements.txt` (Python Dependencies)
```txt
fastapi==0.124.2
sqlmodel==0.0.27
psycopg2-binary==2.9.11
pydantic==2.12.5
pydantic-settings==2.12.0
python-dotenv==1.2.1
```

#### `gymbro-api/app/main.py` (Add root_path)
```python
def create_app() -> FastAPI:
    app = FastAPI(
        title="Gym Bro API",
        lifespan=lifespan,
        root_path="/api",  # Critical: Vercel routes /api/* to this app
    )
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

### Step 3.4: Deploy Backend
The backend deploys automatically with the frontend (single Vercel project).

After deployment, Vercel will:
- Install Python dependencies from `api/requirements.txt`
- Create a serverless function at `/api/handler`
- Route `/api/*` requests to the function

### Step 3.5: Verify Backend
```bash
curl https://your-app.vercel.app/api/health
# Expected: {"status":"ok"}
```

**Common Issues**:
- **404 Not Found**: Check `root_path="/api"` in main.py
- **500 Error**: Check DATABASE_URL is set correctly
- **Module Not Found**: Check api/requirements.txt has all dependencies

---

## Part 4: Testing & Validation

### Test 1: Health Check
```
https://your-app.vercel.app/api/health
```
Expected: `{"status":"ok"}`

### Test 2: Frontend Access
```
https://your-app.vercel.app/
```
Expected: See the Gym Bro UI

### Test 3: Create Check-In
Use the UI or curl:
```bash
curl -X PUT https://your-app.vercel.app/api/daily-checkins/2026-01-19 \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{"weight":180,"steps":8000,"trained":true}'
```

### Test 4: View Logs
Vercel Dashboard → Deployment → Functions → `/api/handler` → Logs

---

## Part 5: Ongoing Maintenance

### Database Backups
Neon provides automatic daily backups (free tier: 7-day retention)

### Monitoring
- Vercel Analytics: Project → Analytics
- Function Logs: Deployment → Functions
- Error Tracking: Deployment → Logs (filter by "error")

### Redeployment
- **Auto**: Push to GitHub → Vercel auto-deploys
- **Manual**: Vercel Dashboard → Deployments → Redeploy

---

## Cost Breakdown (Free Tier Limits)

| Service | Free Tier | Usage | Cost |
|---------|-----------|-------|------|
| Vercel (Hosting) | 100 GB bandwidth/month | ~1-5 GB/month | $0 |
| Vercel (Functions) | 100K invocations/month | ~1-10K/month | $0 |
| Neon (Database) | 3 GB storage | <100 MB | $0 |
| **Total** | | | **$0** |

---

## Troubleshooting

### Backend Returns 404
**Cause**: `root_path` not set in FastAPI app  
**Fix**: Add `root_path="/api"` to FastAPI constructor

### Backend Returns 500
**Cause**: DATABASE_URL missing or invalid  
**Fix**: Check environment variables in Vercel settings

### Database Connection Timeout
**Cause**: Neon database sleeping (free tier)  
**Fix**: First request may be slow (10-15s), subsequent requests fast

### Frontend 404 on Refresh
**Cause**: Vercel routing misconfigured  
**Fix**: Ensure vercel.json has catch-all route to index.html

---

## Next Steps

1. ✅ Test all CRUD operations from UI
2. ⏳ Set up custom domain (optional)
3. ⏳ Enable Vercel Analytics
4. ⏳ Configure error monitoring
5. ⏳ Add Google OAuth (Week 4-6)

### Step 3.4: Deploy Backend
1. Go to Vercel dashboard → "Add New" → "Project"
2. Import `gym-bro` repo again (or select existing)
3. Set root directory: `./gymbro-api`
4. Build: `pip install -r requirements.txt`
5. Output: `.vercel/output`
6. **Environment Variables**:
   - Key: `DATABASE_URL`
   - Value: Your Neon connection string (from Step 1.3)
   - Click "Add"
7. Deploy

### Step 3.5: Verify Backend is Running
```bash
curl https://gym-bro-api.vercel.app/health
# Should return: {"status":"ok"}
```

**✅ If you get {"status":"ok"}, backend is live!**

### Step 3.6: Update Frontend API URL
1. Go to frontend project → Settings → Environment Variables
2. Update:
   ```
   VITE_API_URL=https://gym-bro-api.vercel.app/api
   ```
3. Redeploy frontend

---

## Part 4: Vercel Blob Setup (Photo Storage)

### Step 4.1: Enable Blob
1. Frontend project settings → "Storage" tab
2. Click "Create Database" → "Vercel Blob"
3. Click "Create"
4. Copy token from modal

### Step 4.2: Add Blob to Frontend
```bash
cd gymbro-web
npm install @vercel/blob
```

### Step 4.3: Create Blob Helper
Create `gymbro-web/src/lib/blob.ts`:

```typescript
import { put } from '@vercel/blob';

export async function uploadPhoto(file: File): Promise<string> {
  const blob = await put(`meals/${Date.now()}-${file.name}`, file, {
    access: 'public', // Allow public viewing
  });
  return blob.url;
}
```

### Step 4.4: Add to Backend
Backend will receive presigned URLs from frontend, not files directly.
```python
# In gymbro-api/app/routers/food_logs.py
# Add endpoint to create FoodLog with photo_url
@router.post("/", response_model=FoodLog, status_code=201)
def create_food_log(
    payload: FoodLogCreate,  # Includes photo_url: Optional[str]
    ...
):
    ...
```

---

## Part 5: Database Backups & Data Policy

### Automated Backups (Neon)
1. Neon dashboard → Project settings
2. "Backups" tab → Enable automated backups
3. Free tier: 7-day retention

### Data Deletion Policy
As discussed, old data gets deleted per policy.

To delete data:
```python
# Add endpoint to backend
@router.delete("/data-cleanup")
def cleanup_old_data(session: Session = Depends(get_session)):
    """Delete logs older than 90 days."""
    cutoff_date = date.today() - timedelta(days=90)
    session.query(FoodLog).filter(FoodLog.logged_at < cutoff_date).delete()
    session.commit()
    return {"deleted": "old data"}
```

---

## Part 6: Verify Everything Works

### Test Locally
```bash
# Terminal 1: Backend with Postgres
cd gymbro-api
.venv\Scripts\activate
export DATABASE_URL="your-neon-connection-string"
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd gymbro-web
npm run dev

# Open http://localhost:5173
# Test: Log a meal, workout, check-in
# Verify data persists (refresh page)
```

### Test Production
```bash
# Visit https://yourusername.vercel.app
# Test all flows
# Check Vercel dashboard for errors (Functions logs)
```

---

## Part 7: CI/CD (Auto-Deploy on Push)

Vercel automatically deploys on GitHub push to `main` branch.

**To enable**:
1. Go to Vercel project → Settings → "Git"
2. Ensure "Deploy on push" is enabled
3. Now, every `git push` to `main` deploys automatically

---

## 🚨 Troubleshooting

### "Database connection failed"
- Check `DATABASE_URL` in Vercel env vars
- Verify Neon database is active (Neon dashboard)
- Ensure connection string format is correct

### "CORS error from frontend"
- Backend is at: `https://gym-bro-api.vercel.app`
- Frontend is at: `https://yourusername.vercel.app`
- Different domains → need CORS headers
- Add to `gymbro-api/app/main.py`:
  ```python
  from fastapi.middleware.cors import CORSMiddleware
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://yourusername.vercel.app", "http://localhost:5173"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

### "Cold start too slow"
- Vercel Functions cold start: 1–5 seconds (normal)
- After first request, stays warm for ~15 minutes
- No fix needed; explain in interview: "Acceptable latency for personal use"

### "Blob upload fails"
- Check Vercel Blob is enabled (Storage tab)
- Verify frontend has blob token in env vars
- Check file size <10MB

---

## 📊 Monitoring

### Vercel Dashboard
- Project → Deployments (see all deploys)
- Project → Functions (see backend logs)
- Project → Monitoring (see error rates, latency)

### Neon Dashboard
- Connections (see active connections)
- Query insights (optimize slow queries)

---

## 🎯 Post-Deployment Checklist

- [ ] Frontend loads on https://yourusername.vercel.app
- [ ] Backend API responds on https://gym-bro-api.vercel.app/health
- [ ] Can log check-in, meal, workout from production
- [ ] Data persists across refresh
- [ ] Mobile layout works on phone
- [ ] Service worker registered (DevTools → Application)
- [ ] Lighthouse PWA score >90 (DevTools → Lighthouse)

---

## 🔄 Redeploying After Code Changes

### Local → GitHub
```bash
git add .
git commit -m "feat: add mobile UI improvements"
git push origin main
```

### GitHub → Vercel (Automatic)
- Vercel webhook triggers
- Runs build command
- Deploys within 1–2 minutes
- Check status in Vercel dashboard

---

## 💰 Cost Summary (Free Tier)

| Service | Free Tier | Cost |
|---------|-----------|------|
| Neon PostgreSQL | 3 projects, 3 GB, free compute | $0 |
| Vercel Frontend | Unlimited | $0 |
| Vercel Functions | 100k invocations/month | $0 |
| Vercel Blob | 1000 requests/month, 1 GB | $0 |
| Google Cloud Vision | 1000 requests/month | $0 |
| **Total** | **MVP use case** | **$0/month** |

---

## Next Steps

1. **This week**: Complete database + frontend deployment
2. **Next week**: Deploy backend + test end-to-end
3. **Then**: Add Google SSO auth (Phase 2)
4. **Then**: AI meal photos (Phase 3)

Ready? Let's start! 🚀
