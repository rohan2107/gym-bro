from sqlmodel import SQLModel, create_engine, Session
from .config import settings

# Create engine - echo=False in production for performance
engine = create_engine(
    settings.DATABASE_URL, 
    echo=False,  # Set to True for debugging
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=300,  # Recycle connections after 5 minutes
)


def init_db() -> None:
    """Initialize the database by creating all tables."""
    from . import models  # noqa: F401
    from sqlmodel import select

    SQLModel.metadata.create_all(engine)
    
    # Seed user 1 for MVP (temporary until OAuth is implemented)
    with Session(engine) as session:
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


def get_session():
    """Dependency that provides a database session."""
    with Session(engine) as session:
        yield session
