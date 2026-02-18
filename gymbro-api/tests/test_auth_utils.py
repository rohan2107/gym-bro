"""Tests for authentication utilities."""

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.auth_utils import create_jwt, verify_jwt


def test_create_jwt():
    """Test JWT token creation."""
    user_id = 42
    token = create_jwt(user_id)
    
    assert isinstance(token, str)
    assert len(token) > 0
    assert "." in token  # JWT has three parts separated by dots


def test_verify_jwt_valid():
    """Test JWT verification with valid token."""
    user_id = 42
    token = create_jwt(user_id)
    
    verified_user_id = verify_jwt(token)
    assert verified_user_id == user_id


def test_verify_jwt_invalid():
    """Test JWT verification with invalid token."""
    with pytest.raises(HTTPException) as exc_info:
        verify_jwt("invalid.token.here")
    assert exc_info.value.status_code == 401


def test_verify_jwt_malformed():
    """Test JWT verification with malformed token."""
    with pytest.raises(HTTPException) as exc_info:
        verify_jwt("not-a-jwt")
    assert exc_info.value.status_code == 401


def test_jwt_round_trip():
    """Test creating and verifying multiple tokens."""
    user_ids = [1, 42, 100, 999]
    
    for user_id in user_ids:
        token = create_jwt(user_id)
        verified_id = verify_jwt(token)
        assert verified_id == user_id


def test_jwt_different_tokens_for_same_user():
    """Test that creating multiple tokens for the same user verifies correctly."""
    import time
    user_id = 1
    token1 = create_jwt(user_id)
    time.sleep(0.01)  # Small delay to ensure different timestamp
    token2 = create_jwt(user_id)
    
    # Both should verify to the same user
    assert verify_jwt(token1) == user_id
    assert verify_jwt(token2) == user_id
