# Vercel Deployment Guide - Option A (Ngrok Tunnel)

**Date**: January 13, 2026  
**Strategy**: Deploy frontend to Vercel, expose local backend via ngrok tunnel  
**Time**: ~20 minutes  
**Cost**: $0

---

## 🎯 Goal

Get PWA on iPhone with HTTPS (required for "Add to Home Screen") while keeping backend simple.

**Architecture**:
```
iPhone (HTTPS) → Vercel (Frontend) → Ngrok Tunnel → Your PC (Backend)
```

---

## ✅ Step 1: Configure Frontend for Production

**Changes Made**:
- ✅ Updated `src/lib/api.ts` to use `VITE_API_URL` environment variable
- ✅ Added CORS middleware to backend (`app/main.py`)
- ✅ Configured CORS to allow Vercel domains

**What This Means**:
- Development: Uses `/api` proxy (localhost:8000)
- Production: Uses `VITE_API_URL` (your ngrok URL)

---

## 📦 Step 2: Set Up Ngrok Tunnel

### What is Ngrok?
Ngrok creates a secure tunnel from the internet to your local backend, giving you a public HTTPS URL.

### Install Ngrok

**Option A: Download**:
1. Go to https://ngrok.com/download
2. Download Windows version
3. Extract to a folder (e.g., `C:\tools\ngrok`)
4. Add to PATH or run from folder

**Option B: Chocolatey** (if you have it):
```powershell
choco install ngrok
```

**Option C: Scoop** (if you have it):
```powershell
scoop install ngrok
```

### Create Ngrok Account (Free)
1. Go to https://dashboard.ngrok.com/signup
2. Sign up (free tier is fine)
3. Copy your authtoken from dashboard
4. Run in PowerShell:
```powershell
ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
```

### Start Ngrok Tunnel

**In a new PowerShell window**:
```powershell
# Navigate to where you installed ngrok (or just run if in PATH)
ngrok http 8000
```

**You'll see output like**:
```
ngrok

Session Status                online
Account                       your@email.com
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**Copy the HTTPS URL**: `https://abc123.ngrok-free.app`

⚠️ **Important**: This URL changes every time you restart ngrok (unless you have a paid plan). For testing, this is fine.

---

## 🚀 Step 3: Deploy Frontend to Vercel

### 3.1 Push Code to GitHub

```powershell
# Make sure all changes are committed
git add .
git commit -m "feat: configure frontend for Vercel deployment with ngrok backend"
git push origin main
```

### 3.2 Create Vercel Account

1. Go to https://vercel.com
2. Click "Sign Up"
3. Choose "Continue with GitHub"
4. Authorize Vercel to access your repositories

### 3.3 Import Project

1. Click "Add New" → "Project"
2. Find `gym-bro` in your repositories
3. Click "Import"

### 3.4 Configure Project

**Framework Preset**: Vite

**Root Directory**: `gymbro-web` (click "Edit" and select the folder)

**Build & Output Settings**:
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

**Environment Variables** (click "Add"):
```
Name: VITE_API_URL
Value: https://YOUR_NGROK_URL.ngrok-free.app
```
Replace with your actual ngrok URL (from Step 2)

```
Name: VITE_USER_ID
Value: 1
```

**Click "Deploy"** 🚀

### 3.5 Wait for Deployment

- First build takes ~2-3 minutes
- Vercel will show progress
- When done, you'll get a URL like: `https://gym-bro-username.vercel.app`

---

## ✅ Step 4: Test Deployment

### 4.1 Ensure Backend is Running

In PowerShell (in `gym-bro` directory):
```powershell
# Activate venv
.\gymbro-api\.venv\Scripts\Activate.ps1

# Start backend
cd gymbro-api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify backend is accessible**:
```powershell
curl http://localhost:8000/health
```
Should return: `{"status":"ok"}`

### 4.2 Verify Ngrok is Running

In another PowerShell window:
```powershell
ngrok http 8000
```

**Test ngrok tunnel**:
```powershell
curl https://YOUR_NGROK_URL.ngrok-free.app/health
```
Should return: `{"status":"ok"}`

⚠️ **Note**: First request to ngrok may show a warning page. Click "Visit Site" to proceed.

### 4.3 Test Vercel Deployment

1. Open your Vercel URL: `https://gym-bro-username.vercel.app`
2. Open browser DevTools (F12) → Network tab
3. Try logging a meal or workout
4. Check Network tab - API calls should go to ngrok URL
5. Verify data saves successfully

**If you see CORS errors**:
- Check backend logs for CORS rejections
- Verify ngrok URL is correct in Vercel environment variables
- Restart backend after CORS changes

---

## 📱 Step 5: Test PWA on iPhone

### 5.1 Open in Safari

1. On your iPhone, open Safari
2. Navigate to your Vercel URL: `https://gym-bro-username.vercel.app`
3. The app should load

### 5.2 Install as PWA

1. Tap the Share button (square with arrow)
2. Scroll down and tap "Add to Home Screen"
3. Edit name if desired (e.g., "Gym Bro")
4. Tap "Add"

**You now have a PWA on your iPhone!** 🎉

### 5.3 Test PWA Features

**Test Online**:
- Open the app from home screen
- Log a meal
- Log a workout
- Verify data syncs

**Test Offline**:
1. Enable Airplane Mode on iPhone
2. Open the app
3. App should still load (from cache)
4. You'll see the orange "Offline" banner
5. Try navigating between tabs (should work)
6. Disable Airplane Mode
7. Data should sync when online

---

## 🔧 Troubleshooting

### Problem: Vercel deployment fails

**Solution**: Check build logs in Vercel dashboard
- Common issues: Missing dependencies, TypeScript errors
- Run `npm run build` locally to test

### Problem: API calls fail (CORS errors)

**Solution**: 
1. Check backend logs for CORS rejection
2. Verify Vercel domain is in CORS origins
3. Restart backend after CORS changes
4. Clear browser cache

### Problem: Ngrok URL changed

**Solution**:
1. Get new ngrok URL from terminal
2. Update in Vercel: Project Settings → Environment Variables
3. Redeploy: Deployments → Three dots → Redeploy

### Problem: "Add to Home Screen" not available

**Solution**:
- Must be HTTPS (Vercel provides this)
- Must have manifest.json (we have this)
- Must have service worker (we have this)
- Try Safari only (Chrome iOS doesn't support PWA install)

### Problem: Data not syncing

**Solution**:
1. Check ngrok is running: `curl https://YOUR_NGROK_URL.ngrok-free.app/health`
2. Check backend is running: `curl http://localhost:8000/health`
3. Check browser DevTools → Network tab for failed requests
4. Verify `VITE_API_URL` environment variable in Vercel

---

## 📊 What's Running

**Three Services**:
1. **Backend** (localhost:8000) - Your PC
2. **Ngrok** (https://abc123.ngrok-free.app) - Tunnel to backend
3. **Frontend** (https://gym-bro-username.vercel.app) - Vercel

**Data Flow**:
```
iPhone → Vercel Frontend → Ngrok Tunnel → Your Backend → SQLite Database
```

---

## ⚠️ Limitations of This Setup

**Temporary**:
- Backend only works when your PC is on
- Ngrok URL changes when you restart (free tier)
- Not suitable for sharing with others

**Next Steps (Week 2-3)**:
- Deploy backend to Vercel Functions (permanent)
- Migrate to Neon PostgreSQL (cloud database)
- Get stable URLs for both frontend and backend

**But for now**: You can test PWA on iPhone and validate mobile UX! 🎉

---

## 🎯 Success Checklist

- [ ] Frontend deployed to Vercel
- [ ] Ngrok tunnel running
- [ ] Backend accessible via ngrok
- [ ] PWA installed on iPhone
- [ ] Can log meals/workouts from iPhone
- [ ] Offline mode works
- [ ] Data persists after app restart

---

## 📝 URLs to Save

**Frontend (Vercel)**: `https://gym-bro-username.vercel.app`  
**Backend (Ngrok)**: `https://abc123.ngrok-free.app`  
**Backend (Local)**: `http://localhost:8000`

**Vercel Dashboard**: https://vercel.com/dashboard  
**Ngrok Dashboard**: https://dashboard.ngrok.com

---

## 🔄 Daily Workflow

**Morning (Start Development)**:
```powershell
# Terminal 1: Start backend
cd gym-bro\gymbro-api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start ngrok
ngrok http 8000

# Copy ngrok URL, update in Vercel if changed (unlikely same day)
```

**If ngrok URL changed**:
1. Go to Vercel → Project Settings → Environment Variables
2. Update `VITE_API_URL` with new ngrok URL
3. Trigger redeploy

**Evening (Stop Services)**:
- Ctrl+C in both terminals
- iPhone app will show "Offline" but still works from cache

---

## 📱 Demo for Interviews

**Talking Point**: 
> "I deployed the frontend to Vercel and exposed my local backend via ngrok tunnel. This let me test the PWA on my actual iPhone with HTTPS, which is required for service worker installation. I configured CORS to allow the Vercel domain, and the app works perfectly - even offline. Later, I'll deploy the backend to Vercel Functions for a permanent production setup."

**Shows**:
- Deployment experience
- Problem-solving (HTTPS requirement)
- Understanding of CORS
- Mobile testing
- Pragmatic decisions (ngrok for testing)

---

## Next: Full Production Deployment

See `DEPLOYMENT_GUIDE.md` for deploying backend to Vercel Functions (Week 2-3).
