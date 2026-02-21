"""Shared test fixtures and configuration."""

import sys
from pathlib import Path
import pytest
from fastapi import FastAPI
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
    
    Optimized for fast test execution:
    - In-memory SQLite with static pool
    - Bypasses lifespan events
    - Proper cleanup to avoid hangs
    """
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

    # Create app without lifespan to avoid async overhead in tests
    app = FastAPI(
        title="Gym Bro API (Test)",
        root_path="/api",
    )

    # Add routers (same as create_app but without lifespan)
    from app.routers import (
        health,
        food_logs,
        daily_checkins,
        weight_entries,
        workouts,
        exercise_sets,
        auth,
    )
    
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(food_logs.router)
    app.include_router(daily_checkins.router)
    app.include_router(weight_entries.router)
    app.include_router(workouts.router)
    app.include_router(exercise_sets.router)

    # Override dependencies
    from app.db import get_session
    app.dependency_overrides[get_session] = override_get_session

    # Create test client without raising server exceptions
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    # Cleanup
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(engine)
    engine.dispose()
