"""Dependencies for request handling."""

from fastapi import Header, Cookie, HTTPException, status
from typing import Optional
from app.auth_utils import verify_jwt


def get_user_id(
    auth_token: Optional[str] = Cookie(None),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id")
) -> int:
    """
    Extract user_id from JWT cookie or legacy X-User-Id header.
    
    Supports both authentication methods for backward compatibility:
    1. Cookie-based JWT (preferred for authenticated users)
    2. X-User-Id header (legacy, for testing/development)
    
    Args:
        auth_token: JWT token from cookie (if authenticated)
        x_user_id: Legacy user ID from header
        
    Returns:
        User ID
        
    Raises:
        HTTPException: 401 if no valid authentication provided
    """
    # Try JWT cookie first (preferred method)
    if auth_token:
        try:
            return verify_jwt(auth_token)
        except HTTPException:
            # JWT invalid - fall through to check header
            pass
    
    # Fall back to X-User-Id header (for backward compatibility)
    if x_user_id and x_user_id > 0:
        return x_user_id
    
    # No valid authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please sign in."
    )
