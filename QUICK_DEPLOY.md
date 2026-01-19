# Quick Vercel Deployment Guide

All code changes are complete! Follow these steps to deploy:

## 1️⃣ Set Up Neon PostgreSQL (5 minutes)

1. Go to https://neon.tech and sign up with GitHub
2. Click "Create project"
   - Name: `gym-bro-prod`
   - Region: Choose closest to you (e.g., `us-east-1`)
3. Click "Create"
4. Copy the connection string (starts with `postgresql://...`)

## 2️⃣ Run Database Migration (2 minutes)

In PowerShell:
```powershell
cd gymbro-api
.venv\Scripts\activate

# Set the Neon database URL
$env:DATABASE_URL = "postgresql://user:password@host/db?sslmode=require"

# Run migration to create tables
python migrate_db.py
```

You should see: `✅ Success! Database tables created`

## 3️⃣ Deploy to Vercel (10 minutes)

### Push code to GitHub:
```powershell
cd ..
git add .
git commit -m "feat: configure for Vercel deployment"
git push origin main
```

### Set up Vercel:
1. Go to https://vercel.com and sign up with GitHub
2. Click "Add New" → "Project"
3. Import your `gym-bro` repository
4. Configure **Frontend** deployment:
   - Framework Preset: **Vite**
   - Root Directory: **gymbro-web**
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Environment Variables:
     - `VITE_API_URL` = `https://your-backend-url.vercel.app/api` (we'll update this)
5. Click "Deploy"

### Deploy Backend:
1. In Vercel dashboard, click "Add New" → "Project" again
2. Import `gym-bro` repository again
3. Configure **Backend** deployment:
   - Framework Preset: **Other**
   - Root Directory: **gymbro-api**
   - Build Command: `pip install -r requirements.txt`
   - Environment Variables:
     - `DATABASE_URL` = Your Neon connection string
4. Click "Deploy"

### Link Frontend to Backend:
1. Copy your backend URL (e.g., `https://gym-bro-api.vercel.app`)
2. Go to frontend project → Settings → Environment Variables
3. Update `VITE_API_URL` to `https://gym-bro-api.vercel.app/api`
4. Redeploy frontend (Deployments → Redeploy)

## 4️⃣ Test (5 minutes)

1. Visit your frontend URL: `https://gym-bro-web.vercel.app`
2. Open DevTools → Network tab
3. Try logging a meal/workout
4. Verify API calls go to your backend URL
5. Refresh page - data should persist!

## 5️⃣ Install PWA on iPhone

1. Open your Vercel URL in Safari on iPhone
2. Tap the Share button
3. Scroll down → "Add to Home Screen"
4. Tap "Add"
5. Open the app from your home screen! 🎉

## ✅ Verification Checklist

- [ ] Frontend loads at your Vercel URL
- [ ] Backend responds at `https://your-backend.vercel.app/health`
- [ ] Can create meal/workout from production app
- [ ] Data persists after refresh
- [ ] PWA installs on iPhone
- [ ] Offline indicator works

## 🚨 Troubleshooting

**"Database connection failed"**
- Check DATABASE_URL in backend environment variables
- Verify IP allowlist in Neon (add `0.0.0.0/0` for Vercel)

**"CORS error"**
- Frontend URL must match CORS settings
- Check backend logs in Vercel dashboard

**"Cold start slow"**
- First request takes 3-5 seconds (normal)
- Subsequent requests are fast

---

Need help? Check the existing documentation:
- Full details: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
