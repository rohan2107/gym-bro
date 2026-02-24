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
