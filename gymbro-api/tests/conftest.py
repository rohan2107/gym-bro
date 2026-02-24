"""Shared test fixtures and configuration."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

# Ensure the app package is importable when running tests from project root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client():
    """
    Create test client with in-memory SQLite database.
    
    Uses create_app() to ensure test environment matches production app structure.
    Optimized for fast test execution:
    - In-memory SQLite with static pool
    - Mocked init_db to prevent real database connections
    - Proper cleanup to avoid hangs
    """
    from unittest.mock import patch
    
    # Create in-memory SQLite engine with static pool
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Disable SQL logging for speed
    )

    # Import models to register tables
    from app import models  # noqa: F401

    # Create all tables
    SQLModel.metadata.create_all(engine)

    # Override session dependency
    def override_get_session():
        with Session(engine) as session:
            yield session

    # Mock init_db to prevent database operations during lifespan
    with patch('app.main.init_db'):
        # Use create_app() to get the real app with all middleware/routers
        from app.main import create_app
        app = create_app()

        # Override dependencies
        from app.db import get_session
        app.dependency_overrides[get_session] = override_get_session

        # Create test client
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c

        # Cleanup
        app.dependency_overrides.clear()
    
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def session():
    """
    Create a test database session for unit tests.
    
    This is a standalone session fixture for tests that need database access
    without the full FastAPI app context.
    """
    # Create in-memory SQLite engine with static pool
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Import models to register tables
    from app import models  # noqa: F401

    # Create all tables
    SQLModel.metadata.create_all(engine)

    # Create and yield session
    with Session(engine) as test_session:
        yield test_session

    # Cleanup
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def user_token():
    """
    Create a valid JWT token for test user (user_id=1).
    
    This allows testing authenticated endpoints that expect JWT tokens.
    """
    from app.auth_utils import create_jwt
    return create_jwt(user_id=1)


@pytest.fixture()
def test_user_in_db(client: TestClient):
    """
    Create a test user in the database.
    
    This ensures user_id=1 exists for tests that need a full user record
    (not just authentication).
    """
    from app.models import User
    from app.db import get_session
    
    # Get the test database session
    session_gen = client.app.dependency_overrides[get_session]()
    session = next(session_gen)
    
    try:
        # Create user if doesn't exist
        user = session.get(User, 1)
        if not user:
            user = User(
                id=1,
                email="test@example.com",
                photo_count=0,
                last_photo_date=None
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        yield user
    finally:
        # Close generator to ensure cleanup runs
        session_gen.close()
