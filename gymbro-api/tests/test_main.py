"""Tests for FastAPI app structure and configuration."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(autouse=True)
def mock_init_db(monkeypatch):
    """Mock init_db to avoid database operations in app structure tests."""
    def mock_init():
        pass  # No-op
    
    import app.main
    monkeypatch.setattr(app.main, 'init_db', mock_init)


@pytest.fixture(scope="module")
def app():
    """Create a single app instance for all tests in this module."""
    return create_app()


@pytest.fixture(scope="module")
def test_client(app):
    """Create a single test client for all tests in this module."""
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


def test_lifespan_startup_calls_init_db():
    """Test that lifespan startup attempts to call init_db()."""
    # This test uses a separate monkeypatch, not the autouse fixture
    init_db_called = []
    
    def mock_init_db():
        init_db_called.append(True)
    
    # Create app with custom mock
    import app.main as main_module
    original_init = main_module.init_db
    main_module.init_db = mock_init_db
    
    try:
        app = create_app()
        
        # Trigger lifespan by creating a test client
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/health")
            assert resp.status_code == 200
        
        # Verify init_db was called during startup
        assert len(init_db_called) > 0, "init_db should be called during app startup"
    finally:
        main_module.init_db = original_init


def test_lifespan_handles_init_db_exception():
    """Test that lifespan handles init_db exceptions gracefully."""
    def mock_init_db_that_fails():
        raise Exception("Simulated database error")
    
    # Create app with failing init_db
    import app.main as main_module
    original_init = main_module.init_db
    main_module.init_db = mock_init_db_that_fails
    
    try:
        app = create_app()
        
        # Should not crash, app should still be usable
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/health")
            assert resp.status_code == 200
        
        # If we get here, the error was handled gracefully
        assert True
    finally:
        main_module.init_db = original_init


def test_app_startup_and_shutdown(test_client):
    """Test that app can start up and shut down cleanly."""
    # Make a request to ensure app is functional
    resp = test_client.get("/health")
    assert resp.status_code == 200
    
    # If we get here without hanging, startup/shutdown worked
    assert True


def test_app_handles_requests_with_json_body(test_client):
    """Test that app can handle requests with JSON bodies."""
    # Test a POST endpoint with JSON
    resp = test_client.post(
        "/food-logs/",
        headers={"X-User-Id": "1"},
        json={
            "description": "Test food",
            "calories": 100
        }
    )
    
    # Should process the request (may return 201 or other status)
    assert resp.status_code in [200, 201]
