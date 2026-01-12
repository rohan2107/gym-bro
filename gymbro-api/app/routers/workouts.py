from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, SQLModel, select

from ..db import get_session
from ..deps import get_user_id
from ..models import Workout

router = APIRouter(prefix="/workouts", tags=["workouts"])


class WorkoutCreate(SQLModel):
    """Request model for creating a workout."""
    name: str
    note: Optional[str] = None


@router.get("", response_model=List[Workout])
def list_workouts(
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    query = select(Workout).where(Workout.user_id == user_id).order_by(Workout.started_at.desc())
    return session.exec(query).all()


@router.post("", response_model=Workout, status_code=status.HTTP_201_CREATED)
def create_workout(
    payload: WorkoutCreate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    workout = Workout(
        user_id=user_id,
        name=payload.name,
        note=payload.note,
    )
    session.add(workout)
    session.commit()
    session.refresh(workout)
    return workout


@router.get("/{workout_id}", response_model=Workout)
def get_workout(
    workout_id: int,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    workout = session.exec(
        select(Workout).where(
            Workout.id == workout_id, Workout.user_id == user_id
        )
    ).first()
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return workout


@router.put("/{workout_id}", response_model=Workout)
def update_workout(
    workout_id: int,
    payload: WorkoutCreate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    workout = session.exec(
        select(Workout).where(
            Workout.id == workout_id, Workout.user_id == user_id
        )
    ).first()
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    workout.name = payload.name
    workout.note = payload.note
    session.add(workout)
    session.commit()
    session.refresh(workout)
    return workout


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(
    workout_id: int,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    workout = session.exec(
        select(Workout).where(
            Workout.id == workout_id, Workout.user_id == user_id
        )
    ).first()
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    session.delete(workout)
    session.commit()
