from sqlmodel import SQLModel, create_engine, Session
from .config import settings

# Create the database engine.
# echo=True prints SQL queries to the console; you can turn it off later.
engine = create_engine(settings.DATABASE_URL, echo=True)


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    In production, you'll typically use migrations instead.
    """
    # Import models so SQLModel is aware of them
    from . import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Dependency that provides a database session.
    """
    with Session(engine) as session:
        yield session
