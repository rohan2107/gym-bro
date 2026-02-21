# Phase 4: AI Meal Photo Logging - Implementation Plan

**Status**: 📋 Planning  
**Start Date**: February 18, 2026  
**Estimated Duration**: 3-4 weeks (12-16 working days)  
**Goal**: Enable users to log meals by taking photos with AI-powered food recognition  
**Risk Level**: Medium-High (external API dependencies, UX complexity)

## Evaluation Summary

**Strategic Merit**: High - Reduces friction in nutrition logging, improves retention  
**Technical Risk**: Medium-High - API latency, label→nutrition mapping ambiguity  
**Time Estimates**: Realistic with prioritization and early validation  
**Key Dependencies**: Google Vision API quotas, USDA mapping accuracy, mobile camera support

---

## Overview

### User Flow
1. User opens "Meals" page → taps "📸 Photo" button
2. Camera opens (or file picker on desktop)
3. User takes/selects meal photo
4. Photo uploads to Vercel Blob
5. Backend calls Google Cloud Vision API
6. AI identifies food items
7. Backend queries USDA FoodData for nutrition
8. Frontend shows predictions in review UI
9. User confirms/edits → meal saved to food log

### Success Metrics
- ✅ Photo to predictions in <5 seconds (realistic on cellular networks)
- ✅ Food identification confidence >70% (AI predictions users trust)
- ✅ Works on mobile camera (iOS Safari + Android Chrome tested)
- ✅ Graceful fallback to manual entry (all failure modes covered)
- ✅ Rate limiting prevents cost overrun (30 photos/day/user)
- ✅ Free tier covers typical usage (~33 photos/day total)
- ✅ User can edit/override all AI predictions
- ✅ Handles edge cases (camera denied, bad photo, no food detected)

---

## Architecture

### Tech Stack Additions
- **Vercel Blob**: Photo storage ($0.00 - free tier: 100GB/month)
- **Google Cloud Vision API**: Food detection ($0.00 - free tier: 1000 requests/month)
- **USDA FoodData Central API**: Nutrition lookup ($0.00 - free public API)
- **Environment Variables**: API keys, blob storage tokens

### Data Flow
```
Mobile Camera
    ↓
Frontend (React)
    ↓ POST /food-logs/from-photo (multipart/form-data)
Backend (FastAPI)
    ↓ Upload photo
Vercel Blob Storage
    ↓ Get public URL
Google Cloud Vision API
    ↓ Return food labels
USDA FoodData API
    ↓ Return nutrition per food
Backend aggregates results
    ↓ Return predictions
Frontend Review UI
    ↓ User confirms/edits
POST /food-logs (standard endpoint)
    ↓
Database (PostgreSQL)
```

---

## Pre-Implementation Requirements

### Critical Preparatory Work (Before Phase 4.1)

**1. Food Label → USDA Mapping Spec**

Define how Vision API labels map to USDA database entries:

```yaml
# Example mapping rules
confidence_threshold: 0.70  # Reject predictions below this

label_mappings:
  # Direct matches
  "pizza": "USDA:174987"  # Pizza, cheese, regular crust
  "hamburger": "USDA:173309"  # Ground beef burger
  
  # Synonyms
  "burger": "hamburger"
  "fries": "french fries"
  
  # Compound foods (use average)
  "salad": "USDA:168409"  # Garden salad, average
  
  # Fallback strategy
  unknown_food: "prompt_user_or_generic_estimate"
```

**2. Performance Budget**

| Operation | Target | Max Acceptable |
|-----------|--------|----------------|
| Photo upload | <1s | 2s |
| Vision API | <1.5s | 3s |
| USDA lookup | <500ms | 1s |
| Total pipeline | <3s | 5s |

**Caching strategy**:
- Cache common USDA lookups (Redis/memory, 1 hour TTL)
- Pre-fetch top 100 foods on app load

**3. UX Edge Case Planning**

| Edge Case | User Impact | Mitigation |
|-----------|-------------|------------|
| Camera permission denied | High | Show upload button + clear instructions |
| Poor photo (blurry/dark) | Medium | Offer retake + crop UI |
| Non-food image detected | Medium | Confidence filter + "Try again or log manually" |
| Network timeout | High | Show loading state + retry button |
| API quota exceeded | Medium | "Daily limit reached, try tomorrow" + manual fallback |
| Multiple foods in photo | Low (MVP) | Pick highest confidence item (Phase 4.1), multi-food in Phase 5 |

---

## Implementation Phases

### **Phase 4.1: Infrastructure Setup** (Days 1-3)

**Backend Setup**:
- [ ] Create Google Cloud project + enable Vision API
- [ ] Generate API key (restrict to Vision API only)
- [ ] **Verify quota limits**: Confirm 1000 requests/month free tier
- [ ] Add `GOOGLE_VISION_API_KEY` to `.env` / Vercel env vars
- [ ] Install dependencies: `pip install google-cloud-vision pillow`
- [ ] Test Vision API with 5 sample images (pizza, burger, salad, drink, non-food)
- [ ] Document actual response format and confidence scores

**Vercel Blob Setup**:
- [ ] Enable Vercel Blob in project settings
- [ ] Generate blob token (`BLOB_READ_WRITE_TOKEN`)
- [ ] Add to `.env` and Vercel env vars
- [ ] Install: `npm install @vercel/blob` (if needed)
- [ ] Test upload with sample file

**USDA API Setup**:
- [ ] Register for FoodData Central API key (free)
- [ ] Add `USDA_API_KEY` to `.env`
- [ ] Test endpoint: `https://api.nal.usda.gov/fdc/v1/foods/search?api_key=...`
- [ ] Document rate limits (unlimited, government API)
- [ ] **Build initial mapping table**: Top 50 common foods → USDA IDs
- [ ] Test ambiguous lookups ("burger" vs "hamburger" vs "cheeseburger")

**Dependencies**:
```txt
# Add to gymbro-api/requirements.txt
google-cloud-vision==3.7.0
pillow==10.2.0
python-multipart==0.0.9  # Already included
```

**Environment Variables**:
```bash
# gymbro-api/.env.example
DATABASE_URL=postgresql://user:pass@host/db
JWT_SECRET_KEY=your-jwt-secret
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-secret
GOOGLE_VISION_API_KEY=your-vision-api-key
USDA_API_KEY=your-usda-api-key
BLOB_READ_WRITE_TOKEN=vercel-blob-token
```

---

### **Phase 4.2: Backend Services** (Days 4-7)

**New Files**:
```
gymbro-api/app/
├── services/
│   ├── __init__.py
│   ├── vision.py         # Google Vision API integration
│   ├── nutrition.py      # USDA FoodData lookup
│   └── rate_limiter.py   # Track API usage per user
└── routers/
    └── photo_meals.py    # New endpoint for photo uploads
```

**`app/services/vision.py`**:
```python
"""Google Cloud Vision API integration for food detection."""

from google.cloud import vision
from typing import List
import os

class VisionService:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient(
            client_options={"api_key": os.getenv("GOOGLE_VISION_API_KEY")}
        )
    
    def detect_food(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Detect food items in image with confidence scores.
        
        Returns list of predictions: [
            {"label": "pizza", "confidence": 0.92},
            {"label": "salad", "confidence": 0.78}
        ]
        """
        image = vision.Image(content=image_bytes)
        
        # Use label detection + web detection
        labels_response = self.client.label_detection(image=image)
        web_response = self.client.web_detection(image=image)
        
        # Extract food-related labels with confidence
        predictions = []
        
        for label in labels_response.label_annotations:
            if label.score > 0.70:  # Confidence threshold
                predictions.append({
                    "label": label.description.lower(),
                    "confidence": label.score,
                    "source": "vision_label"
                })
        
        # Add web entities (often more specific)
        for entity in web_response.web_detection.web_entities:
            if entity.score > 0.60:  # Lower threshold for web entities
                predictions.append({
                    "label": entity.description.lower(),
                    "confidence": entity.score,
                    "source": "web_entity"
                })
        
        # Sort by confidence, deduplicate, return top 3
        seen = set()
        unique_predictions = []
        for pred in sorted(predictions, key=lambda x: x["confidence"], reverse=True):
            if pred["label"] not in seen:
                seen.add(pred["label"])
                unique_predictions.append(pred)
                if len(unique_predictions) >= 3:
                    break
        
        return unique_predictions
```

**`app/services/nutrition.py`**:
```python
"""USDA FoodData Central API integration."""

import httpx
from typing import Optional, Dict
import os

class NutritionService:
    BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    
    def __init__(self):
        self.api_key = os.getenv("USDA_API_KEY")
    
    async def search_food(self, query: str) -> Optional[Dict]:
        """
        Search USDA database for food item.
        
        Returns dict with: {
            "name": "Pizza, cheese",
            "calories": 265,
            "protein_g": 11,
            "carbs_g": 33,
            "fat_g": 10
        }
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/foods/search",
                params={
                    "api_key": self.api_key,
                    "query": query,
                    "pageSize": 1,
                    "dataType": ["Survey (FNDDS)"]  # Most accurate data
                }
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data.get("foods"):
                return None
            
            food = data["foods"][0]
            nutrients = {n["nutrientName"]: n["value"] for n in food.get("foodNutrients", [])}
            
            return {
                "name": food["description"],
                "calories": int(nutrients.get("Energy", 0)),
                "protein_g": round(nutrients.get("Protein", 0), 1),
                "carbs_g": round(nutrients.get("Carbohydrate, by difference", 0), 1),
                "fat_g": round(nutrients.get("Total lipid (fat)", 0), 1)
            }
```

**`app/services/rate_limiter.py`**:
```python
"""Rate limiting for AI API calls."""

from sqlmodel import Session, select
from app.models import User
from datetime import date

class RateLimiter:
    DAILY_LIMIT = 30  # Photos per user per day
    
    def __init__(self, session: Session):
        self.session = session
    
    def check_limit(self, user_id: int) -> tuple[bool, int]:
        """
        Check if user has exceeded daily photo limit.
        
        Returns: (can_use, remaining_count)
        """
        # Query user's photo count for today
        # (We'll add photo_count tracking to User model)
        user = self.session.get(User, user_id)
        
        # Reset counter if new day
        today = date.today()
        if user.last_photo_date != today:
            user.photo_count = 0
            user.last_photo_date = today
            self.session.commit()
        
        remaining = self.DAILY_LIMIT - user.photo_count
        can_use = remaining > 0
        
        return can_use, max(0, remaining)
    
    def increment(self, user_id: int):
        """Increment user's daily photo count."""
        user = self.session.get(User, user_id)
        user.photo_count += 1
        self.session.commit()
```

**`app/routers/photo_meals.py`**:
```python
"""Photo-based meal logging endpoints."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel import Session
from app.deps import get_session, get_user_id
from app.services.vision import VisionService
from app.services.nutrition import NutritionService
from app.services.rate_limiter import RateLimiter
from typing import List
import os

router = APIRouter(prefix="/food-logs", tags=["photo-meals"])

vision_service = VisionService()
nutrition_service = NutritionService()

@router.post("/from-photo")
async def create_food_log_from_photo(
    photo: UploadFile = File(...),
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id)
):
    """
    Upload meal photo and get AI predictions.
    
    Returns predictions for user to review before saving.
    """
    # Check rate limit
    limiter = RateLimiter(session)
    can_use, remaining = limiter.check_limit(user_id)
    
    if not can_use:
        raise HTTPException(
            status_code=429,
            detail=f"Daily photo limit reached. Try again tomorrow."
        )
    
    # Read image bytes
    image_bytes = await photo.read()
    
    # Detect food items with Vision API
    food_labels = vision_service.detect_food(image_bytes)
    
    if not food_labels:
        raise HTTPException(
            status_code=400,
            detail="No food detected in image. Please try again or log manually."
        )
    
    # Lookup nutrition for each detected food
    predictions = []
    for label in food_labels:
        nutrition = await nutrition_service.search_food(label)
        if nutrition:
            predictions.append(nutrition)
    
    # Increment usage counter
    limiter.increment(user_id)
    
    return {
        "predictions": predictions,
        "remaining_photos": remaining - 1,
        "confidence": "medium"  # Could calculate based on Vision scores
    }
```

**Model Updates (`app/models.py`)**:
```python
# Add fields to User model for rate limiting
class User(SQLModel, table=True):
    # ... existing fields ...
    photo_count: int = Field(default=0)
    last_photo_date: date | None = Field(default=None)
```

---

### **Phase 4.3: Frontend UI** (Days 8-11)

**New Components**:
```
gymbro-web/src/
├── components/
│   ├── PhotoCapture.tsx      # Camera input + edge case handling
│   └── MealReview.tsx         # Review AI predictions with confidence
└── pages/
    └── MealsPage.tsx          # Add photo button + flow
```

**Device Testing** (CRITICAL - Do Early!):
- [ ] Test camera capture on iOS Safari (Day 8)
- [ ] Test camera capture on Android Chrome (Day 8)
- [ ] Test file upload fallback (desktop)
- [ ] Test camera permission denial flow
- [ ] Test offline behavior (queue uploads)

**`components/PhotoCapture.tsx`**:
```tsx
import { useState } from 'react'

export function PhotoCapture({ onCapture }: { onCapture: (file: File) => void }) {
  const [preview, setPreview] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Show preview
    const reader = new FileReader()
    reader.onload = () => setPreview(reader.result as string)
    reader.readAsDataURL(file)

    onCapture(file)
  }

  return (
    <div className="space-y-4">
      <input
        type="file"
        accept="image/*"
        capture="environment"  // Use rear camera on mobile
        onChange={handleFileChange}
        className="hidden"
        id="photo-input"
      />
      
      {/* Edge case: Camera permission denied */}
      {permissionDenied && (
        <div className="text-red-500 text-sm">
          Camera access required. Please enable in settings.
        </div>
      )}
      
      <label
        htmlFor="photo-input"
        className="block w-full bg-blue-500 text-white py-3 rounded-lg text-center cursor-pointer"
      >
        📸 Take Photo
      </label>

      {preview && (
        <img src={preview} alt="Meal preview" className="w-full rounded-lg" />
      )}
    </div>
  )
}
```

**`components/MealReview.tsx`**:
```tsx
import { useState } from 'react'

type Prediction = {
  name: string
  calories: number
  protein_g: number
  carbs_g: number
  fat_g: number
}

export function MealReview({ 
  predictions, 
  onConfirm, 
  onCancel 
}: { 
  predictions: Prediction[]
  onConfirm: (meal: Prediction) => void
  onCancel: () => void
}) {
  const [selected, setSelected] = useState(predictions[0])

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold">We detected:</h3>
      
      {/* Food selection */}
      <div className="space-y-2">
        {predictions.map((pred, i) => (
          <button
            key={i}
            onClick={() => setSelected(pred)}
            className={`w-full p-4 rounded-lg border-2 text-left ${
              selected === pred ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
            }`}
          >
            <div className="flex justify-between items-start">
              <div className="font-bold">{pred.name}</div>
              <div className="text-xs text-gray-500">
                {Math.round(pred.confidence * 100)}% sure
              </div>
            </div>
            <div className="text-sm text-gray-600">
              {pred.calories} cal | P: {pred.protein_g}g | C: {pred.carbs_g}g | F: {pred.fat_g}g
            </div>
          </button>
        ))}
      </div>

      {/* Edit nutrition (optional) */}
      <div className="space-y-2">
        <label className="block text-sm font-medium">Calories</label>
        <input
          type="number"
          value={selected.calories}
          onChange={(e) => setSelected({...selected, calories: parseInt(e.target.value)})}
          className="w-full p-2 border rounded"
        />
      </div>

      {/* Action buttons */}
      <div className="flex gap-2">
        <button
          onClick={onCancel}
          className="flex-1 py-3 bg-gray-200 rounded-lg"
        >
          Cancel
        </button>
        <button
          onClick={() => onConfirm(selected)}
          className="flex-1 py-3 bg-green-500 text-white rounded-lg"
        >
          ✓ Confirm
        </button>
      </div>
    </div>
  )
}
```

**Update `pages/MealsPage.tsx`**:
```tsx
// Add photo logging flow alongside manual entry
const [showPhotoFlow, setShowPhotoFlow] = useState(false)
const [predictions, setPredictions] = useState([])

const handlePhotoCapture = async (file: File) => {
  const formData = new FormData()
  formData.append('photo', file)
  
  const response = await api.post('/food-logs/from-photo', formData)
  setPredictions(response.predictions)
}

const handleConfirmMeal = async (meal: Prediction) => {
  await api.post('/food-logs', {
    description: meal.name,
    calories: meal.calories,
    protein_g: meal.protein_g,
    carbs_g: meal.carbs_g,
    fat_g: meal.fat_g
  })
  setShowPhotoFlow(false)
  fetchMeals() // Refresh list
}

// In render:
{showPhotoFlow ? (
  predictions.length > 0 ? (
    <MealReview 
      predictions={predictions}
      onConfirm={handleConfirmMeal}
      onCancel={() => setShowPhotoFlow(false)}
    />
  ) : (
    <PhotoCapture onCapture={handlePhotoCapture} />
  )
) : (
  <button onClick={() => setShowPhotoFlow(true)}>
    📸 Log with Photo
  </button>
)}
```

---

### **Phase 4.4: Testing** (Days 12-14)

**Backend Tests** (`tests/test_photo_meals.py`):
```python
def test_photo_upload_success(client: TestClient):
    """Test successful photo upload and prediction."""
    # Mock Vision API response
    # Mock USDA API response
    # Upload test image
    # Assert predictions returned

def test_rate_limit_exceeded(client: TestClient):
    """Test rate limiting after 30 photos."""
    # Upload 30 photos
    # 31st should return 429

def test_no_food_detected(client: TestClient):
    """Test graceful failure when no food in image."""
    # Upload non-food image
    # Assert 400 error

def test_nutrition_service():
    """Test USDA API integration."""
    # Query "pizza"
    # Assert calories, macros present
```

**Frontend Tests** (`src/test/PhotoCapture.test.tsx`):
```tsx
it('opens camera on mobile', () => {
  // Mock file input
  // Assert capture="environment" set
})

it('shows preview after photo taken', () => {
  // Simulate file selection
  // Assert preview image rendered
})

it('calls onCapture with file', () => {
  // Mock file selection
  // Assert onCapture called with File object
})
```

**Integration Testing**:
- [ ] Take photo of pizza → Predictions show "pizza" with >70% confidence
- [ ] Edit calories → Saves edited value
- [ ] Take 30 photos → 31st shows rate limit message
- [ ] Bad photo (no food) → Fallback to manual entry with clear message
- [ ] Slow network → Loading state shows, timeout after 10s
- [ ] Camera permission denied → Upload button shown
- [ ] Multiple foods in photo → Returns highest confidence item
- [ ] Ambiguous food → Multiple options presented

---

### **Phase 4.5: Deployment** (Days 15-16)

**Vercel Configuration**:
```bash
# Add environment variables in Vercel dashboard:
GOOGLE_VISION_API_KEY=xxx
USDA_API_KEY=xxx
BLOB_READ_WRITE_TOKEN=xxx  # Auto-generated by Vercel
```

**Database Migration**:
```bash
# Generate migration for User model changes
cd gymbro-api
alembic revision --autogenerate -m "add photo rate limiting fields to user"
alembic upgrade head
```

**Testing in Production**:
- [ ] Test on real phone camera (iOS + Android)
- [ ] Verify API keys work in production
- [ ] Check rate limiting persists across sessions
- [ ] Monitor error rates (Vercel logs)
- [ ] Test with various food types (pizza, burger, salad, drinks)
- [ ] Monitor Vision API quota usage (Vercel dashboard)
- [ ] Set up alerts at 80% quota usage

**Documentation Updates**:
- [ ] Update README.md with photo feature
- [ ] Document API endpoints in MVP_STATUS.md
- [ ] Add setup instructions for Vision API
- [ ] Update ARCHITECTURE.md with new services

---

## Cost Analysis

### Free Tier Limits
- **Google Vision API**: 1000 requests/month = ~33/day
- **USDA FoodData**: 1000 requests/hour (unlimited daily)
- **Vercel Blob**: 100GB storage (plenty for photos)
- **Estimated usage**: ~1-2 photos/day personally = ~60/month
- **Safety margin**: 16x under free tier limit

### Monitoring
- Track API usage in Vercel logs
- Alert at 80% of monthly quota (800 requests)
- Auto-fallback to manual entry if quota exceeded

---

## Risk Mitigation

### Technical Risks
- **Vision API inaccurate**: User can edit/override predictions
- **USDA data missing**: Fallback to generic estimates or manual entry
- **Rate limit hit**: Graceful degradation to manual entry
- **Photo upload fails**: Retry logic + manual fallback

### UX Risks
- **Slow predictions**: Show loading state, timeout after 5s
- **Bad photos**: Clear error messages + tips for better photos
- **Privacy concerns**: Photos stored temporarily, deleted after processing (optional)

---

## Success Criteria

**Functional**:
- ✅ Can log meal from photo in <10 taps
- ✅ Predictions accurate enough to save time vs manual entry
- ✅ Rate limiting prevents cost overrun
- ✅ Works on mobile camera (iOS + Android)

**Technical**:
- ✅ Photo to predictions latency <3 seconds
- ✅ Backend tests cover vision + nutrition services
- ✅ Frontend tests cover photo capture flow
- ✅ Error handling for all failure modes
- ✅ Zero cost on free tier with typical usage

**Portfolio**:
- ✅ Demonstrates AI/ML integration skills
- ✅ Shows production-ready error handling
- ✅ Impressive demo-able feature
- ✅ Clean code + documentation

---

## Revised Timeline (3-4 weeks)

### Week 1: Infrastructure + Backend
- **Days 1-3**: Setup APIs (Vision, USDA, Vercel Blob) + verify quotas + build mapping table
- **Days 4-7**: Build backend services (VisionService, NutritionService, RateLimiter) + endpoint

### Week 2: Frontend + Early Device Testing
- **Days 8-9**: Build PhotoCapture + MealReview components
- **Day 8**: Test on real iOS/Android devices (CRITICAL)
- **Days 10-11**: Integrate with backend + edge case handling

### Week 3: Testing + Polish
- **Days 12-13**: Write comprehensive tests (backend + frontend + E2E)
- **Day 14**: Integration testing + bug fixes

### Week 4: Deployment + Documentation
- **Day 15**: Deploy to production + real device testing
- **Day 16**: Documentation + monitoring setup

**Contingency**: +2-3 days buffer for unexpected issues (camera edge cases, API quota problems)

---

## Next Steps

1. **Review this plan** - Any changes/additions?
2. **Start Phase 4.1** - Setup Google Vision API + Vercel Blob
3. **Create `.env.example` updates** - Document new env vars
4. **Setup Google Cloud project** - Enable Vision API, generate key

Ready to start Phase 4.1? 🚀
