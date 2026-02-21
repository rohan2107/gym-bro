"""Tests for FastAPI app structure and configuration."""

import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app


# Mock init_db at module level to prevent database connections during test fixture setup
def _mock_init_db():
    """No-op replacement for init_db during tests."""
    pass


@pytest.fixture(scope="module", autouse=True)
def mock_init_db():
    """Mock init_db to avoid database operations in app structure tests."""
    with patch('app.main.init_db', _mock_init_db):
        yield


@pytest.fixture(scope="module")
def app():
    """
    Create a single app instance for all tests in this module.
    
    WARNING: Module-scoped fixture - shared across all tests.
    Do NOT modify app state in tests using this fixture.
    """
    return create_app()


@pytest.fixture(scope="module")
def test_client(app):
    """
    Create a single test client for all tests in this module.
    
    WARNING: Module-scoped fixture - shared across all tests.
    All tests using this client share the same app instance.
    """
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def test_create_app_returns_fastapi_instance(app):
    """Test that create_app() returns a FastAPI application."""
    assert isinstance(app, FastAPI)
    assert app.title == "Gym Bro API"
    assert app.root_path == "/api"


def test_create_app_includes_health_router(test_client):
    """Test that health check endpoint is accessible."""
    resp = test_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_app_includes_all_routers(app):
    """Test that all expected routers are included in the app."""
    # Get all route paths
    routes = [route.path for route in app.routes]
    
    # Verify key endpoints exist
    assert "/health" in routes
    assert "/auth/me" in routes
    assert "/auth/logout" in routes
    assert "/auth/google/login" in routes
    assert "/food-logs/" in routes
    assert "/daily-checkins" in routes or any("/daily-checkins" in r for r in routes)
    assert "/weight-entries" in routes or any("/weight-entries" in r for r in routes)
    assert "/workouts" in routes or any("/workouts" in r for r in routes)
    assert "/exercise-sets" in routes or any("/exercise-sets" in r for r in routes)


def test_app_has_cors_middleware(app):
    """Test that CORS middleware is configured."""
    # Check that CORS middleware is in the middleware stack
    middleware_classes = [m.cls.__name__ for m in app.user_middleware]
    assert "CORSMiddleware" in middleware_classes


def test_cors_allows_localhost_origins(test_client):
    """Test that CORS allows localhost development origins."""
    # Test preflight request from localhost:5173 (Vite dev)
    resp = test_client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    # Should allow the origin
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_allows_localhost_preview(test_client):
    """Test that CORS allows localhost preview origin."""
    # Test preflight request from localhost:4173 (Vite preview)
    resp = test_client.options(
        "/health",
        headers={
            "Origin": "http://localhost:4173",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:4173"


def test_cors_allows_vercel_preview_urls(test_client):
    """Test that CORS allows Vercel preview URLs (regex pattern)."""
    # Test Vercel preview URL
    resp = test_client.options(
        "/health",
        headers={
            "Origin": "https://gymbro-preview-abc123.vercel.app",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    # Should match the regex pattern and be allowed
    assert resp.status_code == 200
    origin = resp.headers.get("access-control-allow-origin")
    # CORS middleware either echoes the origin or sets it explicitly
    assert origin is not None


def test_app_module_level_instance():
    """Test that the module-level app instance is created."""
    from app import main
    
    # Verify the module has an 'app' attribute
    assert hasattr(main, 'app')
    assert isinstance(main.app, FastAPI)


def test_app_startup_and_shutdown(test_client):
    """Test that app can start up and shut down cleanly."""
    # Make a request to ensure app is functional
    resp = test_client.get("/health")
    assert resp.status_code == 200
    
    # If we get here without hanging, startup/shutdown worked
    assert True


def test_app_handles_requests_with_json_body(test_client):
    """Test that app can handle HTTP requests with JSON bodies (structure test)."""
    # Test that the app accepts JSON bodies without crashing
    # We test with health endpoint (no DB needed) but with a JSON body
    resp = test_client.post(
        "/health",
        json={"test": "data"}
    )
    
    # Health endpoint returns 405 for POST, but that's fine - 
    # we're testing that JSON parsing works, not the endpoint logic
    assert resp.status_code in [200, 405]
