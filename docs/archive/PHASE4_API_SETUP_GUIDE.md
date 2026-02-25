# Phase 4.1: API Setup Guide - AI Meal Photo Logging

**Status**: 🔧 Infrastructure Setup  
**Estimated Time**: 2-3 hours  
**Prerequisites**: Google Account, GitHub account with Vercel connected

This guide walks you through setting up the three external APIs needed for Phase 4:
1. Google Cloud Vision API (food detection)
2. USDA FoodData Central API (nutrition lookup)
3. Vercel Blob Storage (photo storage)

---

## Step 1: Google Cloud Vision API Setup

### 1.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Project name: `gym-bro-vision` (or your choice)
4. Click "Create"
5. Wait for project creation (~30 seconds)

### 1.2 Enable Vision API

1. In the Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Cloud Vision API"
3. Click on "Cloud Vision API"
4. Click **Enable** button
5. Wait for API to be enabled (~30 seconds)

### 1.3 Create API Key

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **API key**
3. Copy the API key (starts with `AIza...`)
4. Click **Restrict Key** (recommended for security)
5. Under **API restrictions**:
   - Select "Restrict key"
   - Check only "Cloud Vision API"
6. Click **Save**

### 1.4 Verify Quotas

1. Go to **APIs & Services** → **Enabled APIs**
2. Click "Cloud Vision API"
3. Click "Quotas" tab
4. Verify: **1000 requests/month** free tier
5. Set up quota alert (optional but recommended):
   - Go to **Billing** → **Budgets & alerts**
   - Create alert at 80% usage (800 requests)

### 1.5 Test API Key

```powershell
# Test in PowerShell
$apiKey = "YOUR_API_KEY_HERE"
$imageUrl = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Eq_it-na_pizza-margherita_sep2005_sml.jpg/800px-Eq_it-na_pizza-margherita_sep2005_sml.jpg"

$body = @{
    requests = @(
        @{
            image = @{ source = @{ imageUri = $imageUrl } }
            features = @(
                @{ type = "LABEL_DETECTION"; maxResults = 5 }
            )
        }
    )
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri "https://vision.googleapis.com/v1/images:annotate?key=$apiKey" -Method Post -Body $body -ContentType "application/json"

$response.responses[0].labelAnnotations | Select-Object description, score
```

**Expected output**: Labels like "Pizza", "Food", "Dish" with confidence scores > 0.70

---

## Step 2: USDA FoodData Central API Setup

### 2.1 Register for API Key

1. Go to [USDA FoodData Central API Key Signup](https://fdc.nal.usda.gov/api-key-signup.html)
2. Fill out the form:
   - **Name**: Your name
   - **Email**: Your email
   - **Organization**: Personal / Gym Bro Project
   - **Intended use**: Nutrition lookup for fitness tracking app
3. Click "Request API Key"
4. Check your email for API key (arrives within minutes)
5. Copy the API key

### 2.2 Test API Key

```powershell
# Test in PowerShell
$usdaKey = "YOUR_USDA_API_KEY_HERE"

$response = Invoke-RestMethod -Uri "https://api.nal.usda.gov/fdc/v1/foods/search?api_key=$usdaKey&query=pizza"

# Show first result
$food = $response.foods[0]
Write-Host "Food: $($food.description)"
Write-Host "Calories: $($food.foodNutrients | Where-Object { $_.nutrientName -eq 'Energy' } | Select-Object -ExpandProperty value)"
```

**Expected output**: Food description and calorie information for pizza

### 2.3 Verify Rate Limits

- **Free tier**: 1000 requests/hour (unlimited daily requests)
- **No credit card required**
- **Public government API** (free forever)

---

## Step 3: Vercel Blob Storage Setup

### 3.1 Enable Blob Storage

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your `gym-bro` project
3. Go to **Storage** tab
4. Click **Create Database** → **Blob**
5. Name: `gym-bro-photos` (or your choice)
6. Click **Create**

### 3.2 Get Blob Token

1. After creation, Vercel automatically generates:
   - `BLOB_READ_WRITE_TOKEN` environment variable
2. Go to **Settings** → **Environment Variables**
3. Find `BLOB_READ_WRITE_TOKEN`
4. Copy the value (starts with `vercel_blob_rw_...`)

### 3.3 Verify Free Tier Limits

- **Storage**: 100GB/month (plenty for photos)
- **Bandwidth**: 100GB/month
- **Uploads**: Unlimited
- **Estimated usage**: ~1-2 photos/day = ~50MB/month (well within limits)

---

## Step 4: Configure Local Environment

### 4.1 Create `.env` File

```powershell
# In gymbro-api directory
cd gymbro-api
Copy-Item .env.example .env
```

### 4.2 Update `.env` with API Keys

Edit `gymbro-api/.env`:

```bash
# Database (existing)
DATABASE_URL=postgresql://your-db-connection-string

# JWT (existing)
JWT_SECRET_KEY=your-existing-secret

# Google OAuth (existing)
GOOGLE_CLIENT_ID=your-existing-client-id
GOOGLE_CLIENT_SECRET=your-existing-secret

# Phase 4: NEW - Add these
GOOGLE_VISION_API_KEY=AIza...your-vision-key
USDA_API_KEY=your-usda-key
BLOB_READ_WRITE_TOKEN=vercel_blob_rw_...your-token
```

### 4.3 Configure Vercel Production Environment

1. Go to **Vercel Dashboard** → **gym-bro** → **Settings** → **Environment Variables**
2. Add the following variables for **Production, Preview, and Development**:

| Variable Name | Value |
|---------------|-------|
| `GOOGLE_VISION_API_KEY` | Your Vision API key |
| `USDA_API_KEY` | Your USDA API key |
| `BLOB_READ_WRITE_TOKEN` | Auto-set by Vercel (already there) |

3. Click **Save** after each

---

## Step 5: Install Dependencies

### 5.1 Backend Dependencies

```powershell
# In gymbro-api directory
cd gymbro-api

# Activate virtual environment
.venv\Scripts\activate

# Install new dependencies
pip install google-cloud-vision==3.7.0 pillow==10.2.0

# Or install all requirements
pip install -r requirements.txt
```

### 5.2 Verify Installation

```powershell
# Test imports
python -c "from google.cloud import vision; print('Vision API: OK')"
python -c "from PIL import Image; print('Pillow: OK')"
python -c "import httpx; print('httpx: OK')"
```

All should print "OK"

---

## Step 6: Test Services

### 6.1 Test Vision Service

Create a test script `test_vision.py`:

```python
import asyncio
from pathlib import Path
from app.services.vision import VisionService

async def test_vision():
    service = VisionService()
    
    # Load test image
    image_path = Path("test_images/pizza.jpg")
    if not image_path.exists():
        print("⚠️  Add a pizza.jpg to test_images/ first")
        return
    
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    # Validate image
    validation = service.validate_image(image_bytes)
    print(f"Image validation: {validation}")
    
    # Detect food (will use mock data until API is enabled)
    predictions = service.detect_food(image_bytes)
    print(f"Predictions: {predictions}")

if __name__ == "__main__":
    asyncio.run(test_vision())
```

Run:
```powershell
python test_vision.py
```

### 6.2 Test Nutrition Service

Create `test_nutrition.py`:

```python
import asyncio
from app.services.nutrition import NutritionService

async def test_nutrition():
    service = NutritionService()
    
    # Test search
    result = await service.search_food("pizza")
    print(f"Pizza nutrition: {result}")
    
    # Test mapping
    from app.services.food_mapping import get_search_query
    query = get_search_query("burger")
    print(f"Burger maps to: {query}")

if __name__ == "__main__":
    asyncio.run(test_nutrition())
```

Run:
```powershell
python test_nutrition.py
```

---

## Step 7: Database Migration

### 7.1 Generate Migration

```powershell
cd gymbro-api

# Generate migration for User model changes (photo_count, last_photo_date)
alembic revision --autogenerate -m "add photo rate limiting to user model"
```

### 7.2 Review Migration

Open the generated file in `alembic/versions/` and verify it adds:
- `photo_count` column (integer, default 0)
- `last_photo_date` column (date, nullable)

### 7.3 Apply Migration

```powershell
# Local database
alembic upgrade head

# Production (will auto-run on next Vercel deploy)
```

---

## Step 8: Validation Checklist

Before moving to Phase 4.2 (Backend Implementation), verify:

- [ ] ✅ Google Cloud Vision API enabled
- [ ] ✅ Vision API key created and restricted
- [ ] ✅ Vision API test successful (returns food labels)
- [ ] ✅ USDA API key received via email
- [ ] ✅ USDA API test successful (returns nutrition data)
- [ ] ✅ Vercel Blob storage created
- [ ] ✅ Blob token added to environment variables
- [ ] ✅ `.env` file configured with all keys
- [ ] ✅ Vercel production environment variables set
- [ ] ✅ Dependencies installed (`google-cloud-vision`, `pillow`)
- [ ] ✅ Test imports successful
- [ ] ✅ Database migration generated and applied
- [ ] ✅ Test images added to `test_images/` directory

---

## Cost Summary

| Service | Free Tier | Estimated Monthly Usage | Cost |
|---------|-----------|-------------------------|------|
| Google Vision API | 1000 requests/month | ~60 photos (2/day) | $0.00 |
| USDA FoodData | 1000 requests/hour | ~60 nutrition lookups | $0.00 |
| Vercel Blob | 100GB storage + bandwidth | ~50MB photos | $0.00 |
| **Total** | | | **$0.00** |

**Safety margin**: ~16x under Vision API free tier limit

---

## Troubleshooting

### Vision API Returns 403 Error
- **Cause**: API key not enabled or restricted incorrectly
- **Fix**: Check API restrictions in Google Cloud Console → Credentials

### USDA API Returns Empty Results
- **Cause**: Food not found in database
- **Fix**: Try different search query (check `food_mapping.py` for examples)

### Blob Upload Fails
- **Cause**: Token not set or expired
- **Fix**: Regenerate token in Vercel dashboard → Storage → Blob

### Import Error for `google.cloud.vision`
- **Cause**: Package not installed
- **Fix**: `pip install google-cloud-vision==3.7.0`

---

## Next Steps

Once all validation checks pass, you're ready for:

**Phase 4.2**: Backend Implementation
- Create `/food-logs/from-photo` endpoint
- Integrate Vision + USDA services
- Add rate limiting logic
- Write unit tests

See [PHASE4_AI_MEAL_PLAN.md](PHASE4_AI_MEAL_PLAN.md) for detailed Phase 4.2 instructions.

---

**Questions or issues?** Check the [Phase 4 Implementation Plan](PHASE4_AI_MEAL_PLAN.md) or create a GitHub issue.
