from sqlmodel import SQLModel, create_engine, Session
from .config import settings

# Lazy initialization of engine
_engine = None


def get_engine():
    """Get or create the database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        try:
            _engine = create_engine(
                settings.DATABASE_URL, 
                echo=False,  # Set to True for debugging
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=300,  # Recycle connections after 5 minutes
            )
        except Exception as e:
            print(f"Warning: Failed to create database engine: {e}")
            # Return None or raise - depends on whether this is critical
            raise
    return _engine


def init_db() -> None:
    """Initialize the database by creating all tables."""
    from . import models  # noqa: F401
    from sqlmodel import select

    try:
        db_engine = get_engine()
        SQLModel.metadata.create_all(db_engine)

        # Seed user 1 for MVP (temporary until OAuth is implemented)
        with Session(db_engine) as session:
            existing = session.exec(select(models.User).where(models.User.id == 1)).first()
            if not existing:
                user = models.User(
                    id=1,
                    email="temp@gymbro.app",
                    display_name="MVP User"
                )
                session.add(user)
                session.commit()
                print("Seeded user 1 for MVP")
    except Exception as e:
        print(f"Warning: init_db failed: {e}")


def get_session():
    """Dependency that provides a database session."""
    db_engine = get_engine()
    with Session(db_engine) as session:
        yield session

