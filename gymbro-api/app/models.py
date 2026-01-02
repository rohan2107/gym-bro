from datetime import datetime, date
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	email: str = Field(index=True)
	display_name: Optional[str] = None
	created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class FoodLog(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	user_id: int = Field(foreign_key="user.id", index=True)
	description: Optional[str] = None
	calories: Optional[float] = None
	protein_g: Optional[float] = None
	carbs_g: Optional[float] = None
	fat_g: Optional[float] = None
	logged_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

	nutrient_entries: List["NutrientEntry"] = Relationship(back_populates="food_log")


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

	food_log: Optional[FoodLog] = Relationship(back_populates="nutrient_entries")


class WeightEntry(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	user_id: int = Field(foreign_key="user.id", index=True)
	for_date: date = Field(nullable=False, index=True)
	weight_kg: float = Field(nullable=False)
	note: Optional[str] = None
	logged_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Workout(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	user_id: int = Field(foreign_key="user.id", index=True)
	name: str = Field(nullable=False)
	started_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
	note: Optional[str] = None

	exercise_sets: List["ExerciseSet"] = Relationship(back_populates="workout")


class ExerciseSet(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	workout_id: int = Field(foreign_key="workout.id", index=True)
	exercise_name: str = Field(nullable=False)
	reps: int = Field(nullable=False)
	weight_kg: Optional[float] = None
	rpe: Optional[float] = None
	performed_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

	workout: Optional[Workout] = Relationship(back_populates="exercise_sets")
