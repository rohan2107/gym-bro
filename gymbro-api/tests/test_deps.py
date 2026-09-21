"""Tests for dependency injection and authentication helpers."""

from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import patch
import pytest
from app.deps import get_user_id
from app.auth_utils import create_jwt


def test_get_user_id_with_valid_jwt(client: TestClient):
    """Test get_user_id with valid JWT token."""
    # Create a valid JWT for user 1
    token = create_jwt(1)
    
    # Simulate the dependency with JWT cookie
    user_id = get_user_id(auth_token=token, authorization=None, x_user_id=None)
    assert user_id == 1


def test_get_user_id_with_x_user_id_header(client: TestClient):
    """Test get_user_id with legacy X-User-Id header."""
    # No JWT, only header
    user_id = get_user_id(auth_token=None, authorization=None, x_user_id=42)
    assert user_id == 42


def test_get_user_id_jwt_takes_precedence(client: TestClient):
    """Test that JWT takes precedence over X-User-Id header."""
    token = create_jwt(1)
    
    # Both provided - JWT should win
    user_id = get_user_id(auth_token=token, authorization=None, x_user_id=99)
    assert user_id == 1


def test_get_user_id_fallback_to_header_on_invalid_jwt(client: TestClient):
    """Test fallback to X-User-Id when JWT is invalid."""
    # Invalid JWT should fall back to header
    user_id = get_user_id(auth_token="invalid-token", authorization=None, x_user_id=42)
    assert user_id == 42


def test_get_user_id_rejects_invalid_x_user_id(client: TestClient):
    """Test that negative or zero X-User-Id is rejected."""
    with pytest.raises(HTTPException) as exc_info:
        get_user_id(auth_token=None, authorization=None, x_user_id=0)
    assert exc_info.value.status_code == 401
    
    with pytest.raises(HTTPException) as exc_info:
        get_user_id(auth_token=None, authorization=None, x_user_id=-1)
    assert exc_info.value.status_code == 401


def test_get_user_id_no_authentication(client: TestClient):
    """Test that missing authentication raises 401."""
    with pytest.raises(HTTPException) as exc_info:
        get_user_id(auth_token=None, authorization=None, x_user_id=None)
    
    assert exc_info.value.status_code == 401
    assert "Authentication required" in exc_info.value.detail


def test_get_user_id_with_authorization_header(client: TestClient):
    """Test get_user_id with Authorization header (Bearer token)."""
    token = create_jwt(1)
    
    user_id = get_user_id(
        auth_token=None,
        authorization=f"Bearer {token}",
        x_user_id=None
    )
    assert user_id == 1


def test_get_user_id_authorization_header_multiple_spaces(client: TestClient):
    """Test Authorization header parsing with multiple spaces."""
    token = create_jwt(1)
    
    # Multiple spaces between "Bearer" and token
    user_id = get_user_id(
        auth_token=None,
        authorization=f"Bearer   {token}",  # 3 spaces
        x_user_id=None
    )
    assert user_id == 1


def test_get_user_id_authorization_header_trailing_space(client: TestClient):
    """Test Authorization header parsing with trailing space."""
    token = create_jwt(1)
    
    # Trailing space after token
    user_id = get_user_id(
        auth_token=None,
        authorization=f"Bearer {token} ",  # trailing space
        x_user_id=None
    )
    assert user_id == 1


def test_get_user_id_authorization_header_case_insensitive(client: TestClient):
    """Test that 'bearer' (lowercase) also works."""
    token = create_jwt(1)
    
    user_id = get_user_id(
        auth_token=None,
        authorization=f"bearer {token}",  # lowercase
        x_user_id=None
    )
    assert user_id == 1


def test_get_user_id_x_user_id_blocked_in_production(client: TestClient):
    """Test that X-User-Id header is rejected in production."""
    with patch.dict("os.environ", {"ENVIRONMENT": "production"}):
        with pytest.raises(HTTPException) as exc_info:
            get_user_id(auth_token=None, authorization=None, x_user_id=42)
        assert exc_info.value.status_code == 401


def test_get_user_id_x_user_id_allowed_in_development(client: TestClient):
    """Test that X-User-Id header works in development."""
    with patch.dict("os.environ", {"ENVIRONMENT": "development"}):
        user_id = get_user_id(auth_token=None, authorization=None, x_user_id=42)
        assert user_id == 42


def test_get_user_id_x_user_id_allowed_in_test(client: TestClient):
    """Test that X-User-Id header works in test environment."""
    with patch.dict("os.environ", {"ENVIRONMENT": "test"}):
        user_id = get_user_id(auth_token=None, authorization=None, x_user_id=42)
        assert user_id == 42


def test_dev_auth_disabled_when_environment_is_unset(monkeypatch):
    """Secure by default: no ENVIRONMENT means the header is rejected.

    Production previously accepted X-User-Id from anyone because the variable
    was never set on Vercel and the default was "development".
    """
    from app.config import Settings
    from app.deps import dev_auth_enabled

    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setattr("app.deps.settings", Settings(_env_file=None))

    assert dev_auth_enabled() is False
    with pytest.raises(HTTPException) as exc_info:
        get_user_id(auth_token=None, authorization=None, x_user_id=42)
    assert exc_info.value.status_code == 401


@pytest.mark.parametrize("env", ["development", "test", "Development"])
def test_dev_auth_is_never_enabled_on_vercel(env):
    """Even an explicit ENVIRONMENT=development cannot enable it on a deployment."""
    with patch.dict("os.environ", {"ENVIRONMENT": env, "VERCEL": "1"}):
        with pytest.raises(HTTPException) as exc_info:
            get_user_id(auth_token=None, authorization=None, x_user_id=42)
        assert exc_info.value.status_code == 401


def test_settings_default_environment_is_production(monkeypatch):
    """The default must be the safe one."""
    from app.config import Settings

    monkeypatch.delenv("ENVIRONMENT", raising=False)
    assert Settings(_env_file=None).ENVIRONMENT == "production"


def test_x_user_id_is_rejected_over_http_in_production(client: TestClient):
    """End to end: the header does not authenticate a real request."""
    with patch.dict("os.environ", {"ENVIRONMENT": "production"}):
        response = client.get("/food-logs/", headers={"X-User-Id": "999999999"})
    assert response.status_code == 401


def test_food_recognizer_defaults_to_gemini():
    from app.deps import get_food_recognizer
    from app.services.gemini import GeminiRecognizer

    assert isinstance(get_food_recognizer(), GeminiRecognizer)


def test_food_recognizer_can_be_switched_to_vision_by_configuration(monkeypatch):
    from app.config import settings
    from app.deps import get_food_recognizer
    from app.services.vision import VisionService

    monkeypatch.setattr(settings, "FOOD_RECOGNITION_PROVIDER", "vision")

    assert isinstance(get_food_recognizer(), VisionService)


def test_unknown_food_recognition_provider_fails_at_startup():
    from pydantic import ValidationError

    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(FOOD_RECOGNITION_PROVIDER="not-a-provider")
