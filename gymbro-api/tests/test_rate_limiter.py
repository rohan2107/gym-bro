"""Tests for Rate Limiter service (photo upload rate limiting)."""

import pytest
from datetime import date, timedelta
from sqlmodel import Session

from app.services.rate_limiter import RateLimiter
from app.models import User


def _uid(user: User) -> int:
    """Extract user ID, asserting it is not None (all test users have explicit IDs)."""
    assert user.id is not None
    return user.id


@pytest.fixture
def test_user(session: Session):
    """Create a test user."""
    user = User(
        id=999,
        email="test@example.com",
        photo_count=0,
        last_photo_date=None
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def rate_limiter(session: Session):
    """Create RateLimiter instance."""
    return RateLimiter(session)


class TestRateLimiter:
    """Test suite for RateLimiter service."""

    def test_initialization(self, rate_limiter: RateLimiter) -> None:
        """Test RateLimiter initializes correctly."""
        assert rate_limiter is not None
        assert rate_limiter.MAX_PHOTOS_PER_DAY == 30

    def test_check_limit_new_user(self, rate_limiter: RateLimiter, test_user: User, session: Session) -> None:
        """Test check_limit for user who hasn't uploaded photos yet."""
        result = rate_limiter.check_limit(_uid(test_user))
        
        assert result["allowed"] is True
        assert result["remaining"] == 30
        assert result["limit"] == 30
        tomorrow = date.today() + timedelta(days=1)
        assert result["resets_at"] == str(tomorrow)

    def test_check_limit_within_limit(self, rate_limiter: RateLimiter, test_user: User, session: Session) -> None:
        """Test check_limit when user is within daily limit."""
        # Set user to have uploaded 10 photos today
        test_user.photo_count = 10
        test_user.last_photo_date = date.today()
        session.add(test_user)
        session.commit()
        
        result = rate_limiter.check_limit(_uid(test_user))
        
        assert result["allowed"] is True
        assert result["remaining"] == 20
        assert result["limit"] == 30

    def test_check_limit_at_limit(self, rate_limiter: RateLimiter, test_user: User, session: Session) -> None:
        """Test check_limit when user has reached daily limit."""
        # Set user to have uploaded 30 photos today
        test_user.photo_count = 30
        test_user.last_photo_date = date.today()
        session.add(test_user)
        session.commit()
        
        result = rate_limiter.check_limit(_uid(test_user))
        
        assert result["allowed"] is False
        assert result["remaining"] == 0
        assert result["limit"] == 30

    def test_check_limit_over_limit(self, rate_limiter: RateLimiter, test_user: User, session: Session) -> None:
        """Test check_limit when user is over daily limit (shouldn't happen but test anyway)."""
        # Set user to have uploaded 35 photos today (edge case)
        test_user.photo_count = 35
        test_user.last_photo_date = date.today()
        session.add(test_user)
        session.commit()
        
        result = rate_limiter.check_limit(_uid(test_user))
        
        assert result["allowed"] is False
        assert result["remaining"] == 0  # Can't be negative

    def test_check_limit_resets_on_new_day(self, rate_limiter: RateLimiter, test_user: User, session: Session) -> None:
        """Test that check_limit resets counter on a new day."""
        # Set user to have uploaded 25 photos yesterday
        yesterday = date.today() - timedelta(days=1)
        test_user.photo_count = 25
        test_user.last_photo_date = yesterday
        session.add(test_user)
        session.commit()
        
        result = rate_limiter.check_limit(_uid(test_user))
        
        # Should be reset
        assert result["allowed"] is True
        assert result["remaining"] == 30
        
        # Verify database was updated
        session.refresh(test_user)
        assert test_user.photo_count == 0
        assert test_user.last_photo_date == date.today()

    def test_check_limit_user_not_found(self, rate_limiter: RateLimiter) -> None:
        """Test check_limit raises error for non-existent user."""
        with pytest.raises(ValueError, match="User .* not found"):
            rate_limiter.check_limit(99999)

    def test_increment_success(self, rate_limiter: RateLimiter, test_user: User, session: Session) -> None:
        """Test successful increment of photo count."""
        # Start with 0 photos
        test_user.photo_count = 0
        test_user.last_photo_date = date.today()
        session.add(test_user)
        session.commit()
        
        new_count = rate_limiter.increment(_uid(test_user))
        
        assert new_count == 1
        
        # Verify database was updated
        session.refresh(test_user)
        assert test_user.photo_count == 1

    def test_increment_multiple_times(self, rate_limiter: RateLimiter, test_user: User, session: Session) -> None:
        """Test incrementing photo count multiple times."""
        # Start with 0 photos
        test_user.photo_count = 0
        test_user.last_photo_date = date.today()
        session.add(test_user)
        session.commit()
        
        # Increment 3 times
        for i in range(1, 4):
            count = rate_limiter.increment(_uid(test_user))
            assert count == i

    def test_increment_fails_at_limit(self, rate_limiter: RateLimiter, test_user: User, session: Session) -> None:
        """Test increment raises error when at limit."""
        # Set user at limit
        test_user.photo_count = 30
        test_user.last_photo_date = date.today()
        session.add(test_user)
        session.commit()
        
        with pytest.raises(ValueError, match="Daily photo limit reached"):
            rate_limiter.increment(_uid(test_user))

    def test_increment_fails_over_limit(self, rate_limiter: RateLimiter, test_user: User, session: Session) -> None:
        """Test increment raises error when over limit."""
        # Set user over limit (edge case)
        test_user.photo_count = 35
        test_user.last_photo_date = date.today()
        session.add(test_user)
        session.commit()
        
        with pytest.raises(ValueError, match="Daily photo limit reached"):
            rate_limiter.increment(_uid(test_user))

    def test_increment_resets_on_new_day(self, rate_limiter: RateLimiter, test_user: User, session: Session) -> None:
        """Test increment works after daily reset."""
        # Set user at limit yesterday
        yesterday = date.today() - timedelta(days=1)
        test_user.photo_count = 30
        test_user.last_photo_date = yesterday
        session.add(test_user)
        session.commit()
        
        # Should succeed because it's a new day
        new_count = rate_limiter.increment(_uid(test_user))
        
        assert new_count == 1
        
        # Verify reset occurred
        session.refresh(test_user)
        assert test_user.photo_count == 1
        assert test_user.last_photo_date == date.today()

    def test_full_day_cycle(self, rate_limiter: RateLimiter, test_user: User, session: Session) -> None:
        """Test a full day of photo uploads."""
        # Start fresh
        test_user.photo_count = 0
        test_user.last_photo_date = None
        session.add(test_user)
        session.commit()
        
        # Upload 30 photos (the limit)
        for i in range(1, 31):
            status = rate_limiter.check_limit(_uid(test_user))
            assert status["allowed"] is True
            assert status["remaining"] == 30 - (i - 1)
            
            count = rate_limiter.increment(_uid(test_user))
            assert count == i
        
        # 31st should fail
        status = rate_limiter.check_limit(_uid(test_user))
        assert status["allowed"] is False
        assert status["remaining"] == 0
        
        with pytest.raises(ValueError):
            rate_limiter.increment(_uid(test_user))

    def test_concurrent_users(self, rate_limiter: RateLimiter, session: Session) -> None:
        """Test rate limiting works independently for different users."""
        # Create two users
        user1 = User(
            id=1001,
            email="user1@example.com",
            photo_count=10,
            last_photo_date=date.today()
        )
        user2 = User(
            id=1002,
            email="user2@example.com",
            photo_count=25,
            last_photo_date=date.today()
        )
        session.add(user1)
        session.add(user2)
        session.commit()
        
        # Check limits independently
        status1 = rate_limiter.check_limit(_uid(user1))
        status2 = rate_limiter.check_limit(_uid(user2))
        
        assert status1["remaining"] == 20
        assert status2["remaining"] == 5
        
        # Increment user1 doesn't affect user2
        rate_limiter.increment(_uid(user1))
        
        status1 = rate_limiter.check_limit(_uid(user1))
        status2 = rate_limiter.check_limit(_uid(user2))
        
        assert status1["remaining"] == 19
        assert status2["remaining"] == 5  # Unchanged

    def test_edge_case_null_last_photo_date(self, rate_limiter: RateLimiter, test_user: User, session: Session) -> None:
        """Test handling of null last_photo_date (new user)."""
        test_user.last_photo_date = None
        test_user.photo_count = 0
        session.add(test_user)
        session.commit()
        
        result = rate_limiter.check_limit(_uid(test_user))
        
        assert result["allowed"] is True
        assert result["remaining"] == 30
        
        # After check, date should be set
        session.refresh(test_user)
        assert test_user.last_photo_date == date.today()

    def test_try_increment_atomic_success(self, session: Session, test_user: User) -> None:
        """Test atomic try_increment succeeds when under limit."""
        rate_limiter = RateLimiter(session)
        
        # Start with 0 photos
        test_user.photo_count = 0
        test_user.last_photo_date = date.today()
        session.add(test_user)
        session.commit()
        
        # Try increment should succeed
        result = rate_limiter.try_increment(_uid(test_user))
        
        assert result["allowed"] is True
        assert result["new_count"] == 1
        assert result["remaining"] == 29
        assert result["limit"] == 30
        
        # Verify database updated
        session.refresh(test_user)
        assert test_user.photo_count == 1

    def test_try_increment_atomic_at_limit(self, session: Session, test_user: User) -> None:
        """Test atomic try_increment fails when at limit."""
        rate_limiter = RateLimiter(session)
        
        # Set to limit
        test_user.photo_count = 30
        test_user.last_photo_date = date.today()
        session.add(test_user)
        session.commit()
        
        # Try increment should fail
        with pytest.raises(ValueError) as exc_info:
            rate_limiter.try_increment(_uid(test_user))
        
        assert "limit reached" in str(exc_info.value).lower()
        
        # Verify count not incremented
        session.refresh(test_user)
        assert test_user.photo_count == 30
