from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..db import get_session
from ..models import FoodLog
from ..deps import get_user_id


router = APIRouter(prefix="/food-logs", tags=["food-logs"])


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
