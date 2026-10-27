"""Database Engine and Session Management for ToolNest."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """
    Lazily initialize and return the SQLAlchemy engine.
    Raises DatabaseConfigurationError if DATABASE_URL is not set.
    """
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        db_url = settings.get_sqlalchemy_database_url()
        # Pool recycle is 300s, pre_ping verifies connections before giving them out (ideal for Neon sleeping instances)
        _engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.debug,
        )
        _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Get the configured sessionmaker."""
    if _session_factory is None:
        get_engine()
    assert _session_factory is not None
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session.
    Automatically closes the session when the request finishes.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


def verify_database_connection() -> bool:
    """
    Test connectivity to PostgreSQL by executing a simple SELECT 1.
    Returns True if successful, raises DatabaseConfigurationError or Exception if failed.
    """
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        return result == 1


def reset_engine() -> None:
    """Reset cached engine and session factory (useful in test suites)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
