from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, SQLModel, select

from ..db import get_session
from ..deps import get_user_id
from ..models import ExerciseSet, Workout

router = APIRouter(prefix="/exercise-sets", tags=["exercise-sets"])


class ExerciseSetCreate(SQLModel):
    """Request model for creating an exercise set."""
    workout_id: int
    exercise_name: str
    reps: int
    weight_kg: Optional[float] = None
    rpe: Optional[float] = None


@router.get("", response_model=List[ExerciseSet])
def list_exercise_sets(
    workout_id: int = None,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    query = select(ExerciseSet).join(Workout).where(Workout.user_id == user_id)
    if workout_id:
        query = query.where(ExerciseSet.workout_id == workout_id)
    query = query.order_by(ExerciseSet.performed_at)
    return session.exec(query).all()


@router.post("", response_model=ExerciseSet, status_code=status.HTTP_201_CREATED)
def create_exercise_set(
    payload: ExerciseSetCreate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    workout = session.exec(
        select(Workout).where(
            Workout.id == payload.workout_id, Workout.user_id == user_id
        )
    ).first()
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    exercise_set = ExerciseSet(
        workout_id=payload.workout_id,
        exercise_name=payload.exercise_name,
        reps=payload.reps,
        weight_kg=payload.weight_kg,
        rpe=payload.rpe,
    )
    session.add(exercise_set)
    session.commit()
    session.refresh(exercise_set)
    return exercise_set


@router.put("/{set_id}", response_model=ExerciseSet)
def update_exercise_set(
    set_id: int,
    payload: ExerciseSetCreate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    exercise_set = session.exec(
        select(ExerciseSet).join(Workout).where(
            ExerciseSet.id == set_id, Workout.user_id == user_id
        )
    ).first()
    if not exercise_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise set not found")
    exercise_set.exercise_name = payload.exercise_name
    exercise_set.reps = payload.reps
    exercise_set.weight_kg = payload.weight_kg
    exercise_set.rpe = payload.rpe
    session.add(exercise_set)
    session.commit()
    session.refresh(exercise_set)
    return exercise_set


@router.delete("/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise_set(
    set_id: int,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_user_id),
):
    exercise_set = session.exec(
        select(ExerciseSet).join(Workout).where(
            ExerciseSet.id == set_id, Workout.user_id == user_id
        )
    ).first()
    if not exercise_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise set not found")
    session.delete(exercise_set)
    session.commit()
