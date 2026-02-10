"""Authentication router for Google OAuth and JWT management."""

from fastapi import APIRouter, Cookie, HTTPException, Response, Depends, status
from sqlmodel import Session, select
import httpx
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
from urllib.parse import urlencode

from app.db import get_session
from app.models import User
from app.auth_utils import create_jwt, verify_jwt

router = APIRouter()

# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@router.get("/me")
def get_current_user(
    auth_token: str = Cookie(None),
    session: Session = Depends(get_session)
):
    """
    Get currently authenticated user.
    
    Validates JWT token and returns user profile.
    """
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user_id = verify_jwt(auth_token)
    user = session.get(User, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "picture_url": user.picture_url,
        "google_id": user.google_id
    }


@router.post("/logout")
def logout(response: Response):
    """Clear authentication cookie."""
    response.delete_cookie(
        key="auth_token",
        path="/",
        domain=None
    )
    return {"message": "Logged out successfully"}


@router.get("/google/login")
async def google_login():
    """
    Initiate Google OAuth flow.
    
    Returns the Google authorization URL for redirect.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    redirect_uri = f"{FRONTEND_URL}/auth/callback"
    
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }
    
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    return {"url": google_auth_url}


@router.get("/google/callback")
async def google_callback(
    code: str,
    session: Session = Depends(get_session),
    response: Response = None
):
    """
    Handle Google OAuth callback.
    
    Exchanges authorization code for tokens, creates/updates user,
    and sets authentication cookie.
    """
    if not all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET]):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    redirect_uri = f"{FRONTEND_URL}/auth/callback"
    
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
        
        id_token_str = tokens.get("id_token")
        if not id_token_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No ID token in response"
            )
        
        # Verify ID token
        idinfo = id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
        
        # Extract user info
        google_id = idinfo["sub"]
        email = idinfo.get("email")
        display_name = idinfo.get("name")
        picture_url = idinfo.get("picture")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google"
            )
        
        # Find or create user
        statement = select(User).where(User.google_id == google_id)
        user = session.exec(statement).first()
        
        if not user:
            # Create new user
            user = User(
                google_id=google_id,
                email=email,
                display_name=display_name,
                picture_url=picture_url
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            # Update existing user info
            user.email = email
            user.display_name = display_name
            user.picture_url = picture_url
            session.add(user)
            session.commit()
            session.refresh(user)
        
        # Generate JWT and set cookie
        token = create_jwt(user.id)
        is_production = "vercel.app" in FRONTEND_URL or "https://" in FRONTEND_URL
        
        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,
            secure=is_production,
            samesite="lax",
            max_age=7 * 24 * 60 * 60,  # 7 days
            path="/"
        )
        
        return {
            "message": "Authentication successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name
            },
            "redirect_url": FRONTEND_URL
        }
        
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange authorization code: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID token: {str(e)}"
        )
