# Deployment Guide: Vercel + Neon + Vercel Blob

**Goal**: Deploy your app to production on Vercel (free tier)  
**Time**: 45 minutes for first-time setup  
**Cost**: $0 for MVP usage

---

## 📋 Prerequisites

- [ ] GitHub account (required for Vercel)
- [ ] GitHub Student Pack (for Vercel credits, optional but helpful)
- [ ] GitHub Student Pack claim: https://education.github.com/pack

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

## Part 2: Vercel Setup (Frontend + Backend)

### Step 2.1: Create Vercel Account & Link GitHub
1. Go to https://vercel.com
2. Click "Sign Up" → "Continue with GitHub"
3. Authorize Vercel
4. Create team name or use personal

### Step 2.2: Import Frontend Project
1. Click "Add New" → "Project"
2. Find `gym-bro` repository in list
3. Click "Import"

**Configure import**:
- Framework: "Next.js" (or Other)
  - Actually, Vite isn't in the list; we'll use "Other"
- Root directory: `./gymbro-web`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variables: **Leave empty for now**

**Click "Deploy"** (will fail, that's OK — we need to set env vars)

### Step 2.3: Set Environment Variables (Frontend)
After deployment fails:
1. Go to project settings → "Environment Variables"
2. Add:
   ```
   VITE_API_URL=https://gym-bro-api.vercel.app/api
   ```
   (Replace with your actual backend URL once deployed)
3. Redeploy (click "Deployments" → "Redeploy")

---

## Part 3: Backend Deployment (Vercel Functions)

### Challenge: FastAPI on Vercel Functions
Vercel Functions run serverless code, but FastAPI is a traditional ASGI app. We need an adapter.

### Step 3.1: Install Vercel ASGI Handler
```bash
cd gymbro-api
pip install vercel-asgi
```

### Step 3.2: Create `api/handler.py`
Create new file: `gymbro-api/api/handler.py`

```python
"""Vercel serverless handler for FastAPI app."""
from vercel_asgi import asgi_handler
from app.main import app

# Vercel calls this function for every request
handler = asgi_handler(app)
```

### Step 3.3: Update Vercel Config
Create `vercel.json` in repo root:

```json
{
  "builds": [
    {
      "src": "gymbro-api/requirements.txt",
      "use": "@vercel/python"
    },
    {
      "src": "gymbro-web/package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "gymbro-api/api/handler.py"
    },
    {
      "src": "/(.*)",
      "dest": "gymbro-web/.vercel/output/static/$1"
    }
  ],
  "env": {
    "DATABASE_URL": "@database_url"
  }
}
```

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
