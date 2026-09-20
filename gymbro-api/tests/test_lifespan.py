"""Tests for FastAPI app lifespan events (startup/shutdown).

These tests are separate from test_main.py because they need to test
the real lifespan behavior without the autouse mock fixture.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app


def test_lifespan_startup_checks_db_connection():
    """Test that lifespan startup verifies the database connection."""
    with patch('app.main.check_db_connection', return_value=True) as mock_check:
        app = create_app()

        # Trigger lifespan by creating a test client
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/health")
            assert resp.status_code == 200

        assert mock_check.called, "check_db_connection should be called during startup"


def test_lifespan_starts_when_db_is_unreachable():
    """The app must still serve requests if the startup DB check fails.

    check_db_connection() swallows its own errors, so an unreachable database
    degrades to a warning rather than a failed cold start.
    """
    with patch('app.main.check_db_connection', return_value=False) as mock_check:
        app = create_app()

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/health")
            assert resp.status_code == 200

        assert mock_check.called
