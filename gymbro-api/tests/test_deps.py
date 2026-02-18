"""Tests for dependency injection and authentication helpers."""

from fastapi.testclient import TestClient
from fastapi import HTTPException
import pytest
from app.deps import get_user_id
from app.auth_utils import create_jwt


def test_get_user_id_with_valid_jwt(client: TestClient):
    """Test get_user_id with valid JWT token."""
    # Create a valid JWT for user 1
    token = create_jwt(1)
    
    # Simulate the dependency with JWT cookie
    user_id = get_user_id(auth_token=token, x_user_id=None)
    assert user_id == 1


def test_get_user_id_with_x_user_id_header(client: TestClient):
    """Test get_user_id with legacy X-User-Id header."""
    # No JWT, only header
    user_id = get_user_id(auth_token=None, x_user_id=42)
    assert user_id == 42


def test_get_user_id_jwt_takes_precedence(client: TestClient):
    """Test that JWT takes precedence over X-User-Id header."""
    token = create_jwt(1)
    
    # Both provided - JWT should win
    user_id = get_user_id(auth_token=token, x_user_id=99)
    assert user_id == 1


def test_get_user_id_fallback_to_header_on_invalid_jwt(client: TestClient):
    """Test fallback to X-User-Id when JWT is invalid."""
    # Invalid JWT should fall back to header
    user_id = get_user_id(auth_token="invalid-token", x_user_id=42)
    assert user_id == 42


def test_get_user_id_rejects_invalid_x_user_id(client: TestClient):
    """Test that negative or zero X-User-Id is rejected."""
    with pytest.raises(HTTPException) as exc_info:
        get_user_id(auth_token=None, x_user_id=0)
    assert exc_info.value.status_code == 401
    
    with pytest.raises(HTTPException) as exc_info:
        get_user_id(auth_token=None, x_user_id=-1)
    assert exc_info.value.status_code == 401


def test_get_user_id_no_authentication(client: TestClient):
    """Test that missing authentication raises 401."""
    with pytest.raises(HTTPException) as exc_info:
        get_user_id(auth_token=None, x_user_id=None)
    
    assert exc_info.value.status_code == 401
    assert "Authentication required" in exc_info.value.detail
