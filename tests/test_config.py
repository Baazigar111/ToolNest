"""Tests for configuration settings and limit validation."""

import pytest

from app.config import DatabaseConfigurationError, Settings


def test_default_limits_adhere_to_prd():
    """Verify that default settings reflect the PRD and zero-cost constraints."""
    settings = Settings(DATABASE_URL="postgresql://user:pass@localhost:5432/db")

    # PRD limits
    assert settings.image_max_bytes == 5 * 1024 * 1024  # 5 MB
    assert settings.pdf_max_bytes == 10 * 1024 * 1024  # 10 MB
    assert settings.request_max_bytes == 15 * 1024 * 1024  # 15 MB
    assert settings.max_files_per_request == 5
    assert settings.max_pdf_merge_split_pages == 100
    assert settings.max_pdf_compress_pages == 50
    assert settings.max_pdf_to_image_pages == 15
    assert settings.max_image_side_px == 6000
    assert settings.max_image_pixels == 25_000_000
    assert settings.max_processing_seconds == 45
    assert settings.rate_limit_per_minute == 20
    assert settings.daily_server_uses_per_visitor == 20
    assert settings.heavy_job_wait_timeout_seconds == 20


def test_cors_origins_resolution():
    """Verify CORS origins calculation including frontend origin and additions."""
    settings = Settings(
        frontend_origin="https://toolnest.pages.dev",
        cors_allowed_origins="https://customdomain.com, https://test.pages.dev",
        environment="production",
    )
    origins = settings.cors_origins
    assert "https://toolnest.pages.dev" in origins
    assert "https://customdomain.com" in origins
    assert "https://test.pages.dev" in origins


def test_database_url_validation_missing():
    """Verify DatabaseConfigurationError is raised when DATABASE_URL is missing or empty."""
    settings = Settings(DATABASE_URL=None)
    with pytest.raises(DatabaseConfigurationError, match="DATABASE_URL is not configured"):
        settings.get_sqlalchemy_database_url()

    settings_empty = Settings(DATABASE_URL="   ")
    with pytest.raises(DatabaseConfigurationError, match="DATABASE_URL is not configured"):
        settings_empty.get_sqlalchemy_database_url()


def test_database_url_formatting():
    """Verify postgresql URL is properly prefixed with psycopg driver."""
    settings_neon = Settings(DATABASE_URL="postgres://user:pass@ep-demo.neon.tech/toolnest")
    assert settings_neon.get_sqlalchemy_database_url().startswith("postgresql+psycopg://")

    settings_pg = Settings(DATABASE_URL="postgresql://user:pass@ep-demo.neon.tech/toolnest")
    assert settings_pg.get_sqlalchemy_database_url().startswith("postgresql+psycopg://")
