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

from app.main import create_app
from app.db import get_session


@pytest.fixture()
def client():
    """
    Create test client with in-memory SQLite database.
    
    Properly manages database lifecycle:
    - Creates engine with connection pooling
    - Sets up test database schema
    - Overrides app dependencies
    - Cleans up connections after test
    """
    # Create in-memory SQLite engine with static pool
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Import models to register tables
    from app import models  # noqa: F401

    # Create all tables
    SQLModel.metadata.create_all(engine)

    # Override session dependency
    def override_get_session():
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_get_session

    # Create test client
    with TestClient(app) as c:
        yield c

    # Cleanup: drop tables and dispose engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()
