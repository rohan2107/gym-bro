"""Dependencies for request handling."""

import os

from fastapi import Header, Cookie, HTTPException, status, Depends
from typing import Optional
from sqlmodel import Session
from app.auth_utils import verify_jwt
from app.config import settings
from app.services.food_recognition import FoodRecognizer
from app.services.gemini import GeminiRecognizer
from app.services.vision import VisionService
from app.services.nutrition import NutritionService
from app.services.rate_limiter import RateLimiter
from app.db import get_session


def running_on_vercel() -> bool:
    """True on any Vercel deployment (production or preview).

    Vercel sets VERCEL=1 itself, so this cannot be forgotten the way an
    application-level ENVIRONMENT variable can.
    """
    return bool(os.getenv("VERCEL"))


def dev_auth_enabled() -> bool:
    """Whether the X-User-Id header may authenticate a request.

    That header lets the caller act as any user, so it must never be reachable
    in a deployed app. It is enabled only when ENVIRONMENT is explicitly
    "development" or "test", and never on Vercel regardless of ENVIRONMENT.
    An unset variable means disabled.
    """
    if running_on_vercel():
        return False
    env = (os.getenv("ENVIRONMENT") or settings.ENVIRONMENT).lower()
    return env in ("development", "test")


def get_user_id(
    auth_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id")
) -> int:
    """
    Extract user_id from JWT (cookie or Authorization header) or legacy X-User-Id header.
    
    Supports multiple authentication methods:
    1. Authorization: Bearer <token> header (REST API standard)
    2. Cookie-based JWT (for browser clients) 
    3. X-User-Id header (dev/test only, disabled in production)
    
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
    
    # Fall back to X-User-Id header (dev/test only, disabled in production)
    if x_user_id and x_user_id > 0 and dev_auth_enabled():
        return x_user_id
    
    # No valid authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please sign in."
    )


def get_food_recognizer() -> FoodRecognizer:
    """
    Provide the configured food-recognition provider.

    The provider is chosen by ``FOOD_RECOGNITION_PROVIDER``; each falls back to mock mode
    when its credentials are missing.
    """
    if settings.FOOD_RECOGNITION_PROVIDER == "vision":
        return VisionService()
    return GeminiRecognizer()


def get_nutrition_service(session: Session = Depends(get_session)) -> NutritionService:
    """
    Provide NutritionService instance for nutrition lookup.

    Since M1.0 this queries a local reference table (see ADR-0010), not an external API, so
    there is no key to be missing and no mock mode: it works the same in every environment.
    """
    return NutritionService(session)


def get_rate_limiter(session: Session = Depends(get_session)) -> RateLimiter:
    """
    Provide RateLimiter instance for photo upload rate limiting.
    
    Args:
        session: Database session (injected)
        
    Returns:
        RateLimiter instance
    """
    return RateLimiter(session)
