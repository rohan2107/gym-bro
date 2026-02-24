import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlmodel import Session, SQLModel, select

from ..db import get_session
from ..models import FoodLog
from ..deps import get_user_id, get_vision_service, get_nutrition_service, get_rate_limiter
from ..services.vision import VisionService
from ..services.nutrition import NutritionService
from ..services.rate_limiter import RateLimiter
from ..services.food_mapping import get_search_query


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/food-logs", tags=["food-logs"])


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
    vision_service: VisionService = Depends(get_vision_service),
    nutrition_service: NutritionService = Depends(get_nutrition_service),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> Dict[str, Any]:
    """Analyze a meal photo and return nutrition predictions.
    
    This endpoint:
    1. Validates the uploaded image
    2. Checks the user's rate limit (30 photos/day)
    3. Detects food items using Google Cloud Vision API
    4. Looks up nutrition data from USDA FoodData Central
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
                        "calories": 265,
                        "protein_g": 11.0,
                        "carbs_g": 33.0,
                        "fat_g": 10.0
                    }
                }
            ],
            "rate_limit": {
                "remaining": 29,
                "limit": 30,
                "used_today": 1
            },
            "image_info": {
                "format": "JPEG",
                "size_kb": 125
            }
        }
    """
    # Validate content type
    if photo.content_type and not photo.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an image file."
        )
    
    # Read image bytes
    try:
        image_bytes = await photo.read()
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
    
    # Validate file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB."
        )
    
    # Validate image
    validation = vision_service.validate_image(image_bytes)
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
        food_labels = vision_service.detect_food(image_bytes)
    except ValueError as e:
        # Invalid image format or data
        logger.warning(f"Invalid image for food detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Please upload a valid photo."
        )
    except Exception as e:
        # Vision API or unexpected errors
        logger.error(f"Food detection service error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Food detection service temporarily unavailable. Please try again."
        )
    
    if not food_labels:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No food items detected in image. Try a clearer photo or enter manually."
        )
    
    # Map labels to USDA queries and fetch nutrition
    predictions = []
    for label_data in food_labels:
        label = label_data["label"]
        confidence = label_data["confidence"]
        
        # Map label to USDA search query
        search_query = get_search_query(label)
        
        # Look up nutrition from USDA
        try:
            nutrition = await nutrition_service.search_food(search_query)
            
            if nutrition:
                predictions.append({
                    "label": label,
                    "confidence": confidence,
                    "nutrition": nutrition
                })
        except Exception as e:
            # Log error but continue with other predictions
            logger.warning(f"Nutrition lookup failed for '{label}': {e}")
            continue
    
    # If no nutrition data found for any labels
    if not predictions:
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

