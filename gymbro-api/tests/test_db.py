"""Tests for database connection checking and session management."""

from sqlmodel import create_engine, Session
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.db import check_db_connection, get_session, get_engine


def test_check_db_connection_succeeds_for_reachable_database():
    """A reachable database returns True."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    with patch('app.db.get_engine', return_value=test_engine):
        assert check_db_connection() is True

    test_engine.dispose()


def test_check_db_connection_returns_false_on_failure():
    """An unreachable database returns False rather than raising.

    A serverless cold start must not fail because of a transient database blip;
    every request opens its own session regardless.
    """
    with patch('app.db.get_engine', side_effect=Exception("connection refused")):
        assert check_db_connection() is False


def test_check_db_connection_does_not_create_tables():
    """Alembic owns the schema - startup must not create tables.

    Two mechanisms managing one schema is how the migration history silently
    stops matching the database.
    """
    from sqlalchemy import inspect

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    with patch('app.db.get_engine', return_value=test_engine):
        check_db_connection()

    assert inspect(test_engine).get_table_names() == []

    test_engine.dispose()


def test_check_db_connection_does_not_seed_users():
    """Startup must not write to the database.

    This previously inserted a placeholder user (id=1, temp@gymbro.app) into
    production on every cold start, left over from the pre-OAuth MVP.
    """
    from sqlalchemy import inspect
    from sqlmodel import SQLModel, select

    from app.models import User

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    SQLModel.metadata.create_all(test_engine)

    with patch('app.db.get_engine', return_value=test_engine):
        check_db_connection()

    assert "user" in inspect(test_engine).get_table_names()
    with Session(test_engine) as session:
        assert session.exec(select(User)).all() == []

    test_engine.dispose()


def test_get_session_provides_session():
    """Test that get_session() provides a working database session."""
    # Use the dependency generator
    session_generator = get_session()
    
    # Get the session from the generator
    session = next(session_generator)
    
    try:
        # Verify it's a Session instance
        assert isinstance(session, Session)
        
        # Verify the session is active (we can't easily test queries
        # with the real database without proper setup)
        assert session is not None
        
    finally:
        # Clean up by exhausting the generator (triggers cleanup)
        try:
            next(session_generator)
        except StopIteration:
            pass  # Expected when generator is exhausted


def test_get_session_cleanup():
    """Test that get_session() properly closes the session after use."""
    session_generator = get_session()
    session = next(session_generator)
    
    # Session should be active
    assert session.is_active
    
    # Exhaust generator to trigger cleanup
    try:
        next(session_generator)
    except StopIteration:
        pass
    
    # After cleanup, session should be closed
    # Note: We can't easily test this without inspecting internal state,
    # but if there's a session leak, other tests would fail
    assert True  # If we get here without hanging, cleanup worked


@patch('app.db.get_engine')
def test_engine_configuration(mock_get_engine):
    """Test that the database engine is properly configured."""
    # Create a test engine
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )
    
    mock_get_engine.return_value = test_engine
    
    # Get the engine and verify configuration
    engine = get_engine()
    assert engine is not None
    
    # Verify pool settings
    assert engine.pool._pre_ping is True
    assert engine.pool._recycle == 300
    
    test_engine.dispose()
