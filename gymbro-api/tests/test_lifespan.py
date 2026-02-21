"""Tests for FastAPI app lifespan events (startup/shutdown).

These tests are separate from test_main.py because they need to test
the real lifespan behavior without the autouse mock_init_db fixture.
"""

from fastapi.testclient import TestClient

from app.main import create_app


def test_lifespan_startup_calls_init_db():
    """Test that lifespan startup attempts to call init_db()."""
    init_db_called = []
    
    def mock_init_db():
        init_db_called.append(True)
    
    # Mock init_db before creating the app
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
    
    # Mock init_db to fail before creating the app
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
