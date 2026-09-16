from sqlmodel import create_engine, Session
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


def check_db_connection() -> bool:
    """Verify the database is reachable.

    Schema creation is deliberately *not* done here. Alembic owns the schema
    (applied by the ``db-migrate`` CI job on push to main); calling
    ``SQLModel.metadata.create_all()`` at startup would make two mechanisms
    responsible for the same thing, and it silently diverges from the migration
    history the moment a migration does anything more than add a table.

    Returns:
        True if a connection could be opened, False otherwise. Never raises —
        a serverless cold start should not fail because of a transient database
        blip, and every request opens its own session anyway.
    """
    from sqlalchemy import text

    try:
        db_engine = get_engine()
        with db_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Warning: database connection check failed: {e}")
        return False


def get_session():
    """Dependency that provides a database session."""
    db_engine = get_engine()
    with Session(db_engine) as session:
        yield session
