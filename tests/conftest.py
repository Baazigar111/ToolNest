"""Pytest test configuration and fixtures for ToolNest."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.db import reset_engine
from app.main import create_app
from app.models import Base


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set testing environment variables before tests execute."""
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "true")
    # Clear cached settings so monkeypatched env applies
    get_settings.cache_clear()
    reset_engine()
    yield
    reset_engine()
    get_settings.cache_clear()


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sqlite_engine():
    """In-memory SQLite engine for testing SQLAlchemy models and operations without PostgreSQL."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(sqlite_engine):
    """Transactional session bound to in-memory SQLite database."""
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def admin_client(sqlite_engine, monkeypatch):
    """FastAPI TestClient with SQLAdmin attached to SQLite test database."""
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)
    monkeypatch.setattr("app.admin.setup.get_session_factory", lambda: session_factory)
    app = create_app(engine=sqlite_engine)
    with TestClient(app) as test_client:
        yield test_client
