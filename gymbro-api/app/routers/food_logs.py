from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import FoodLog


router = APIRouter(prefix="/food-logs", tags=["food-logs"])


@router.get("/", response_model=List[FoodLog])
def list_food_logs(session: Session = Depends(get_session)):
    return session.exec(select(FoodLog)).all()


@router.post("/", response_model=FoodLog, status_code=201)
def create_food_log(food_log: FoodLog, session: Session = Depends(get_session)):
    # For MVP, accept FoodLog body directly; later validate user_id/auth
    session.add(food_log)
    session.commit()
    session.refresh(food_log)
    return food_log
