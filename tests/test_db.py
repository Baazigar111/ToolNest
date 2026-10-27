"""Tests for database engine lifecycle and connection error handling."""

import pytest

from app.config import DatabaseConfigurationError, get_settings
from app.db import get_engine, reset_engine


def test_get_engine_without_database_url_raises_error(monkeypatch):
    """Verify that attempting to create engine without DATABASE_URL raises clear error."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    reset_engine()

    with pytest.raises(DatabaseConfigurationError, match="DATABASE_URL is not configured"):
        get_engine()
