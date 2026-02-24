"""Rate limiting for photo meal logging to prevent API quota overrun.

Tracks photo uploads per user per day and enforces a 30 photos/day limit
to stay under Google Vision API free tier (1000 requests/month).

Uses atomic database operations to prevent race conditions in concurrent requests.
"""

from datetime import date, timedelta
from typing import Any, Dict
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

    def check_limit(self, user_id: int) -> Dict[str, Any]:
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
        # Use row-level locking to prevent race conditions
        user = self.session.exec(
            select(User).where(User.id == user_id).with_for_update()
        ).first()
        
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

    def try_increment(self, user_id: int) -> Dict[str, Any]:
        """Atomically check limit and increment if allowed.
        
        This method performs check + increment in a single transaction to prevent
        race conditions. Uses PostgreSQL row-level locking (FOR UPDATE) for 
        concurrent safety.
        
        **Concurrency Guarantees:**
        - PostgreSQL/MySQL: True row-level locking, highly concurrent
        - SQLite: Database-level locking (FOR UPDATE ignored), still safe but less scalable
        
        **Critical Invariant:** count <= MAX_PHOTOS_PER_DAY under all concurrent access
        
        Args:
            user_id: User ID to increment
            
        Returns:
            Dict with:
            {
                "allowed": True (always True if this returns),
                "new_count": int,
                "remaining": int,
                "limit": int
            }
            
        Raises:
            ValueError: If user not found or limit exceeded
            
        **Transaction Safety:**
        - SELECT FOR UPDATE acquires row lock (PostgreSQL/MySQL)
        - Reset, check, and increment all in single transaction
        - This is the primary method for rate limiting; increment() exists for
          non-atomic use cases but should be avoided in request paths that need
          strict limit enforcement
        """
        # Lock the user row for the entire transaction
        # On PostgreSQL: Acquires exclusive row lock, blocks other transactions
        # On SQLite: No-op, but database-level locking still provides safety
        user = self.session.exec(
            select(User).where(User.id == user_id).with_for_update()
        ).first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        today = date.today()
        
        # Reset counter if it's a new day (still within same transaction)
        if user.last_photo_date != today:
            user.photo_count = 0
            user.last_photo_date = today
        
        # Check limit before incrementing
        if user.photo_count >= self.MAX_PHOTOS_PER_DAY:
            # Raise error - transaction will rollback automatically
            raise ValueError(
                f"Daily photo limit reached ({self.MAX_PHOTOS_PER_DAY}). "
                f"Resets at {date.today() + timedelta(days=1)}."
            )
        
        # Increment atomically (still in same transaction)
        user.photo_count += 1
        new_count = user.photo_count
        self.session.add(user)
        # Single commit completes the entire atomic operation
        self.session.commit()
        
        return {
            "allowed": True,
            "new_count": new_count,
            "remaining": max(0, self.MAX_PHOTOS_PER_DAY - new_count),
            "limit": self.MAX_PHOTOS_PER_DAY,
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
        # Use row-level locking to prevent race conditions
        user = self.session.exec(
            select(User).where(User.id == user_id).with_for_update()
        ).first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        today = date.today()
        
        # Reset counter if it's a new day
        if user.last_photo_date != today:
            user.photo_count = 0
            user.last_photo_date = today
        
        # Check limit
        if user.photo_count >= self.MAX_PHOTOS_PER_DAY:
            raise ValueError(
                f"Daily photo limit reached ({self.MAX_PHOTOS_PER_DAY}). "
                "Please try again tomorrow."
            )
        
        # Increment count
        user.photo_count += 1
        self.session.add(user)
        self.session.commit()
        
        return user.photo_count

    def decrement(self, user_id: int) -> int:
        """Decrement photo count for user (refund).
        
        Used to refund a user's quota when a photo upload fails after
        the rate limit was already incremented.
        
        Args:
            user_id: User ID to decrement
            
        Returns:
            New photo count for today
            
        Raises:
            ValueError: If user not found
        """
        user = self.session.exec(
            select(User).where(User.id == user_id).with_for_update()
        ).first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Only decrement if count is > 0
        if user.photo_count > 0:
            user.photo_count -= 1
            self.session.add(user)
            self.session.commit()
        
        return user.photo_count

    def get_usage_stats(self, user_id: int) -> Dict[str, Any]:
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
