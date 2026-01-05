from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    display_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class FoodLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    checkin_id: Optional[int] = Field(
        default=None, foreign_key="daily_check_in.id", index=True
    )

    description: Optional[str] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    logged_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    nutrient_entries: list["NutrientEntry"] = Relationship(
        back_populates="food_log", sa_relationship=True
    )
    daily_check_in: "DailyCheckIn | None" = Relationship(
        back_populates="food_logs", sa_relationship=True
    )


class NutrientEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    food_log_id: int = Field(foreign_key="foodlog.id", index=True)

    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    food_log: "FoodLog | None" = Relationship(
        back_populates="nutrient_entries", sa_relationship=True
    )


class WeightEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    checkin_id: Optional[int] = Field(
        default=None, foreign_key="daily_check_in.id", index=True
    )

    for_date: date = Field(nullable=False, index=True)
    weight_kg: float = Field(nullable=False)
    note: Optional[str] = None
    logged_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    daily_check_in: "DailyCheckIn | None" = Relationship(
        back_populates="weight_entries", sa_relationship=True
    )


class Workout(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    checkin_id: Optional[int] = Field(
        default=None, foreign_key="daily_check_in.id", index=True
    )

    name: str = Field(nullable=False)
    started_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    note: Optional[str] = None

    exercise_sets: list["ExerciseSet"] = Relationship(
        back_populates="workout", sa_relationship=True
    )
    daily_check_in: "DailyCheckIn | None" = Relationship(
        back_populates="workouts", sa_relationship=True
    )


class ExerciseSet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workout_id: int = Field(foreign_key="workout.id", index=True)

    exercise_name: str = Field(nullable=False)
    reps: int = Field(nullable=False)
    weight_kg: Optional[float] = None
    rpe: Optional[float] = None
    performed_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    workout: "Workout | None" = Relationship(
        back_populates="exercise_sets", sa_relationship=True
    )


class DailyCheckIn(SQLModel, table=True):
    __tablename__ = "daily_check_in"
    __table_args__ = (UniqueConstraint("user_id", "checkin_date"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    checkin_date: date = Field(index=True)

    weight: Optional[float] = None
    trained: bool = False
    steps: Optional[int] = None
    protein_met: bool = False
    notes: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    food_logs: list["FoodLog"] = Relationship(
        back_populates="daily_check_in", sa_relationship=True
    )
    workouts: list["Workout"] = Relationship(
        back_populates="daily_check_in", sa_relationship=True
    )
    weight_entries: list["WeightEntry"] = Relationship(
        back_populates="daily_check_in", sa_relationship=True
    )
