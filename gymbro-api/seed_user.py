"""Seed initial user for MVP (temporary until OAuth is implemented)."""
from app.db import engine
from app.models import User
from sqlmodel import Session, select


def seed_user():
    """Create user with id=1 if it doesn't exist."""
    with Session(engine) as session:
        # Check if user 1 exists
        existing = session.exec(select(User).where(User.id == 1)).first()
        if existing:
            print(f"User 1 already exists: {existing.email}")
            return

        # Create user 1
        user = User(
            id=1,
            email="temp@gymbro.app",
            display_name="Temporary User (MVP)"
        )
        session.add(user)
        session.commit()
        print(f"Created user 1: {user.email}")


if __name__ == "__main__":
    seed_user()
