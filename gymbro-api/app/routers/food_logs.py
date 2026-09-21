import asyncio
import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlmodel import Session, SQLModel, select

from ..db import get_session
from ..models import FoodLog
from ..deps import (
    get_user_id,
    get_food_recognizer,
    get_nutrition_service,
    get_rate_limiter,
    running_on_vercel,
)
from ..services.food_recognition import FoodRecognizer
from ..services.image_validation import validate_image
from ..services.nutrition import NutritionService, estimate_to_nutrition, scale_to_portion
from ..services.rate_limiter import RateLimiter
from ..services.food_mapping import get_search_query


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/food-logs", tags=["food-logs"])

# How long one USDA lookup may take, retries included. USDA is a helper here, not the answer: a
# slow or failing lookup falls back to the model's own estimate rather than holding the user up.
NUTRITION_LOOKUP_BUDGET_SECONDS = 10.0


class FoodLogUpdate(SQLModel):
    """Payload model for updating a food log - only includes updatable fields."""
    description: str
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None


@router.get("/", response_model=List[FoodLog])
def list_food_logs(
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    query = select(FoodLog).where(FoodLog.user_id == user_id)
    return session.exec(query).all()


@router.post("/", response_model=FoodLog, status_code=201)
def create_food_log(
    food_log: FoodLog,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    food_log.user_id = user_id
    session.add(food_log)
    session.commit()
    session.refresh(food_log)
    return food_log


@router.post("/from-photo", status_code=200)
async def create_food_log_from_photo(
    photo: UploadFile = File(...),
    user_id: int = Depends(get_user_id),
    food_recognizer: FoodRecognizer = Depends(get_food_recognizer),
    nutrition_service: NutritionService = Depends(get_nutrition_service),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> Dict[str, Any]:
    """Analyze a meal photo and return nutrition predictions.
    
    This endpoint:
    1. Validates the uploaded image
    2. Checks the user's rate limit (30 photos/day)
    3. Detects food items with the configured recognition provider
    4. Grounds each food in USDA FoodData Central, scaled to the estimated portion, and falls
       back to the model's own estimate (marked ``ai_estimate``) if USDA fails or has no match
    5. Returns predictions for user review/editing
    
    The frontend should display these predictions and allow the user
    to edit/confirm before saving to the food log.
    
    Returns:
        {
            "predictions": [
                {
                    "label": "pizza",
                    "confidence": 0.85,
                    "nutrition": {
                        "name": "Pizza, cheese, regular crust",
                        "calories": 530,          # for the estimated portion
                        "protein_g": 22.0,
                        "carbs_g": 66.0,
                        "fat_g": 20.0,
                        "serving_size": "200g",   # "100g" when no portion was estimated
                        "source": "usda"          # or "ai_estimate" (no USDA data was used)
                    }
                }
            ],
            "rate_limit": {
                "remaining": 29,
                "limit": 30,
                "used_today": 1
            },
            "image_info": {
                "format": "jpeg",
                "size_kb": 125
            }
        }
    """
    # Mock mode returns fixed sample data (always "pizza"). That is right for
    # local development and tests, but on a real deployment it would present
    # fabricated nutrition as an analysis of the user's photo. Refuse instead,
    # before any quota is spent; the UI falls back to manual entry.
    if running_on_vercel() and (food_recognizer.mock_mode or nutrition_service.mock_mode):
        logger.error("Photo analysis requested but API keys are not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Photo analysis is not available right now. Please log this meal manually.",
        )

    # Validate content type
    if photo.content_type and not photo.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an image file."
        )
    
    # Read image bytes with streaming size limit to prevent memory exhaustion
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    image_bytes = b""
    try:
        while True:
            chunk = await photo.read(1024 * 64)  # 64KB chunks
            if not chunk:
                break
            image_bytes += chunk
            if len(image_bytes) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB."
                )
    except HTTPException:
        raise
    except (OSError, ValueError) as e:
        logger.warning(f"Failed to read uploaded image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read image file. Please try again."
        )
    except Exception as e:
        logger.error(f"Unexpected error reading image file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process uploaded file. Please try again."
        )
    
    # Validate image
    validation = validate_image(image_bytes)
    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation["error"]
        )
    
    # Check and reserve rate limit slot atomically
    # This prevents race conditions - we increment BEFORE doing expensive work
    try:
        rate_result = rate_limiter.try_increment(user_id)
    except ValueError as e:
        # Limit exceeded
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    
    # Detect food items
    try:
        food_labels = await food_recognizer.detect_food(
            image_bytes, mime_type=f"image/{validation['format']}"
        )
    except ValueError as e:
        # Invalid image format or data - user error, no refund
        logger.warning(f"Invalid image for food detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Please upload a valid photo."
        )
    except Exception as e:
        # Provider or unexpected errors - refund the quota
        logger.error(f"Food detection service error: {e}", exc_info=True)
        rate_limiter.decrement(user_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Food detection service temporarily unavailable. Please try again."
        )
    
    if not food_labels:
        # No food detected - refund the quota
        rate_limiter.decrement(user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No food items detected in image. Try a clearer photo or enter manually."
        )
    
    # Ground each food in USDA (per 100g, scaled to the estimated portion when there is one).
    # Lookups run concurrently and each is time-boxed. When USDA fails or has no match, the
    # model's own estimate is used instead and labelled as an AI estimate, so a USDA problem
    # degrades accuracy instead of ending the request.
    lookups = await asyncio.gather(
        *(
            asyncio.wait_for(
                nutrition_service.search_food(get_search_query(item["label"])),
                NUTRITION_LOOKUP_BUDGET_SECONDS,
            )
            for item in food_labels
        ),
        return_exceptions=True,
    )

    predictions: List[Dict[str, Any]] = []
    lookup_failed = False
    for item, usda in zip(food_labels, lookups):
        label = item["label"]
        grams = item.get("portion_g")
        estimate = item.get("estimate")

        if isinstance(usda, BaseException):
            # A failed lookup is not the same as "no match". The exception text is not logged
            # because an httpx error carries the request URL.
            lookup_failed = True
            logger.warning(f"Nutrition lookup failed for '{label}': {type(usda).__name__}")
            usda = None

        if usda:
            nutrition = scale_to_portion(usda, grams) if grams else dict(usda)
            nutrition["source"] = "usda"
        elif estimate and grams:
            nutrition = estimate_to_nutrition(label, grams, estimate)
            nutrition["source"] = "ai_estimate"
        else:
            continue

        predictions.append({
            "label": label,
            "confidence": item["confidence"],
            "nutrition": nutrition,
        })

    # Nothing usable from USDA or from the model
    if not predictions:
        # Nothing to show - refund the quota
        rate_limiter.decrement(user_id)
        if lookup_failed:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Nutrition lookup is temporarily unavailable. Please try again, or log this meal manually."
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find nutrition data for detected foods. Try manual entry."
        )

    # Rate limit was already incremented atomically at the start
    # Return the current status
    return {
        "predictions": predictions,
        "rate_limit": {
            "remaining": rate_result["remaining"],
            "limit": rate_result["limit"],
            "used_today": rate_result["new_count"]
        },
        "image_info": {
            "format": validation.get("format"),
            "size_kb": validation.get("size_kb")
        }
    }


@router.get("/{log_id}", response_model=FoodLog)
def get_food_log(
    log_id: int,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    food_log = session.exec(
        select(FoodLog).where(
            FoodLog.id == log_id, FoodLog.user_id == user_id
        )
    ).first()
    if not food_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food log not found")
    return food_log


@router.put("/{log_id}", response_model=FoodLog)
def update_food_log(
    log_id: int,
    payload: FoodLogUpdate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    food_log = session.exec(
        select(FoodLog).where(
            FoodLog.id == log_id, FoodLog.user_id == user_id
        )
    ).first()
    if not food_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food log not found")
    
    food_log.description = payload.description
    food_log.calories = payload.calories
    food_log.protein_g = payload.protein_g
    food_log.carbs_g = payload.carbs_g
    food_log.fat_g = payload.fat_g
    
    session.add(food_log)
    session.commit()
    session.refresh(food_log)
    return food_log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food_log(
    log_id: int,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    food_log = session.exec(
        select(FoodLog).where(
            FoodLog.id == log_id, FoodLog.user_id == user_id
        )
    ).first()
    if not food_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food log not found")
    session.delete(food_log)
    session.commit()

