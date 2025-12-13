from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	email: str = Field(index=True)
	display_name: Optional[str] = None
	created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

	# Relationship placeholder (not needed for basic creation)


class FoodLog(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	user_id: int = Field(foreign_key="user.id")
	# Basic fields for MVP; images handled via storage references later
	description: Optional[str] = None
	calories: Optional[float] = None
	protein_g: Optional[float] = None
	carbs_g: Optional[float] = None
	fat_g: Optional[float] = None
	logged_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
