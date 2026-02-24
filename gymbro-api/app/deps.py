"""Dependencies for request handling."""

from fastapi import Header, Cookie, HTTPException, status, Depends
from typing import Optional
from sqlmodel import Session
from app.auth_utils import verify_jwt
from app.services.vision import VisionService
from app.services.nutrition import NutritionService
from app.services.rate_limiter import RateLimiter
from app.db import get_session


def get_user_id(
    auth_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id")
) -> int:
    """
    Extract user_id from JWT (cookie or Authorization header) or legacy X-User-Id header.
    
    Supports multiple authentication methods for backward compatibility:
    1. Authorization: Bearer <token> header (REST API standard)
    2. Cookie-based JWT (for browser clients) 
    3. X-User-Id header (legacy, for testing/development)
    
    Args:
        auth_token: JWT token from cookie (if authenticated)
        authorization: Authorization header with Bearer token
        x_user_id: Legacy user ID from header
        
    Returns:
        User ID
        
    Raises:
        HTTPException: 401 if no valid authentication provided
    """
    # Try Authorization header first (REST API standard)
    if authorization:
        scheme, _, param = authorization.partition(" ")
        if scheme.lower() == "bearer":
            token = param.strip()
            if token:
                try:
                    return verify_jwt(token)
                except HTTPException:
                    # JWT invalid - fall through to try other methods
                    pass
    
    # Try JWT cookie (for browser clients)
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


def get_vision_service() -> VisionService:
    """
    Provide VisionService instance for food detection.
    
    Returns:
        VisionService instance with auto-detected mock mode
    """
    return VisionService()


def get_nutrition_service() -> NutritionService:
    """
    Provide NutritionService instance for nutrition lookup.
    
    Returns:
        NutritionService instance with auto-detected mock mode
    """
    return NutritionService()


def get_rate_limiter(session: Session = Depends(get_session)) -> RateLimiter:
    """
    Provide RateLimiter instance for photo upload rate limiting.
    
    Args:
        session: Database session (injected)
        
    Returns:
        RateLimiter instance
    """
    return RateLimiter(session)
