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
