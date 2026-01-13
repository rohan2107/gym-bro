from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, SQLModel, select

from ..db import get_session
from ..models import FoodLog
from ..deps import get_user_id


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

