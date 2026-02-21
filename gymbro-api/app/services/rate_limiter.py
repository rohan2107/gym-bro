"""Rate limiting for photo meal logging to prevent API quota overrun.

Tracks photo uploads per user per day and enforces a 30 photos/day limit
to stay under Google Vision API free tier (1000 requests/month).
"""

from datetime import date, datetime
from typing import Dict
from sqlmodel import Session, select

from ..models import User


class RateLimiter:
    """Service for tracking and enforcing photo upload rate limits."""

    MAX_PHOTOS_PER_DAY = 30  # Conservative limit for free tier

    def __init__(self, session: Session):
        """Initialize rate limiter with database session.
        
        Args:
            session: SQLModel database session
        """
        self.session = session

    def check_limit(self, user_id: int) -> Dict[str, any]:
        """Check if user has remaining photo quota for today.
        
        Args:
            user_id: User ID to check
            
        Returns:
            Dict with:
            {
                "allowed": True/False,
                "remaining": int (photos left today),
                "limit": int (total daily limit),
                "resets_at": "YYYY-MM-DD" (when quota resets)
            }
        """
        user = self.session.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        today = date.today()
        
        # Reset counter if it's a new day
        if user.last_photo_date != today:
            user.photo_count = 0
            user.last_photo_date = today
            self.session.add(user)
            self.session.commit()
        
        remaining = max(0, self.MAX_PHOTOS_PER_DAY - user.photo_count)
        
        return {
            "allowed": remaining > 0,
            "remaining": remaining,
            "limit": self.MAX_PHOTOS_PER_DAY,
            "resets_at": str(today),
        }

    def increment(self, user_id: int) -> int:
        """Increment photo count for user.
        
        Args:
            user_id: User ID to increment
            
        Returns:
            New photo count for today
            
        Raises:
            ValueError: If user not found or limit exceeded
        """
        status = self.check_limit(user_id)
        
        if not status["allowed"]:
            raise ValueError(
                f"Daily photo limit reached ({self.MAX_PHOTOS_PER_DAY}). "
                "Please try again tomorrow."
            )
        
        user = self.session.get(User, user_id)
        user.photo_count += 1
        self.session.add(user)
        self.session.commit()
        
        return user.photo_count

    def get_usage_stats(self, user_id: int) -> Dict[str, any]:
        """Get usage statistics for user.
        
        Args:
            user_id: User ID to check
            
        Returns:
            Dict with usage stats:
            {
                "photos_today": int,
                "photos_remaining": int,
                "last_photo_date": "YYYY-MM-DD" or None,
            }
        """
        user = self.session.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        today = date.today()
        
        # If last photo was on a different day, count is 0
        if user.last_photo_date != today:
            photos_today = 0
        else:
            photos_today = user.photo_count
        
        return {
            "photos_today": photos_today,
            "photos_remaining": max(0, self.MAX_PHOTOS_PER_DAY - photos_today),
            "last_photo_date": str(user.last_photo_date) if user.last_photo_date else None,
        }
