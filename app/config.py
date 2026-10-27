"""Application Configuration for ToolNest using Pydantic Settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfigurationError(Exception):
    """Raised when database access is requested but DATABASE_URL is not configured."""


class Settings(BaseSettings):
    """ToolNest global settings loaded from environment variables and defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Environment
    environment: str = Field(default="development", description="Runtime environment (development, production, testing)")
    debug: bool = Field(default=False, description="Debug mode flag")
    app_name: str = Field(default="ToolNest", description="Application branding name")
    api_base_url: str = Field(default="http://localhost:8000", description="Public URL of the FastAPI backend")

    # Frontend and CORS
    frontend_origin: str = Field(
        default="http://localhost:3000",
        description="Public site origin (Cloudflare Pages URL or custom domain)",
    )
    cors_allowed_origins: str = Field(
        default="",
        description="Comma-separated additional CORS allowed origins",
    )

    # Database
    database_url: str | None = Field(
        default=None,
        validation_alias="DATABASE_URL",
        description="Neon PostgreSQL connection URL",
    )

    # Admin Authentication & Security
    admin_secret_key: str = Field(
        default="toolnest-default-dev-secret-key-32charsmin",
        validation_alias="ADMIN_SECRET_KEY",
        description="Cryptographic secret key for signing admin sessions",
    )
    session_cookie_name: str = Field(
        default="toolnest_admin_session",
        description="Name of the signed session cookie",
    )
    cookie_secure: bool = Field(
        default=False,
        description="Enforce Secure flag on cookies (set to True in production)",
    )

    # Free Tier Limits (PRD Section 5.4 & Section 8)
    image_max_bytes: int = Field(default=5 * 1024 * 1024, description="5 MB max per image")
    pdf_max_bytes: int = Field(default=10 * 1024 * 1024, description="10 MB max per PDF")
    request_max_bytes: int = Field(default=15 * 1024 * 1024, description="15 MB max per total request")
    max_files_per_request: int = Field(default=5, description="Maximum files per request")
    max_pdf_merge_split_pages: int = Field(default=100, description="Max PDF pages for merge and split")
    max_pdf_compress_pages: int = Field(default=50, description="Max PDF pages for compress")
    max_pdf_to_image_pages: int = Field(default=15, description="Max PDF pages for PDF-to-image")
    max_image_side_px: int = Field(default=6000, description="Maximum image width or height in pixels")
    max_image_pixels: int = Field(default=25_000_000, description="Maximum total pixel count (25 megapixels)")
    max_processing_seconds: int = Field(default=45, description="Maximum processing time in seconds before timeout")
    rate_limit_per_minute: int = Field(default=20, description="Per-IP rate limit per minute")
    daily_server_uses_per_visitor: int = Field(default=20, description="Free server tool uses per day per visitor")
    heavy_job_wait_timeout_seconds: int = Field(default=20, description="Max seconds to wait for heavy job slot")

    # Static Site Publishing (Phase 3 placeholders)
    github_token: str | None = Field(
        default=None,
        validation_alias="GITHUB_TOKEN",
        description="Narrowly scoped GitHub token for committing to generated-site repo",
    )
    github_repository: str | None = Field(
        default=None,
        validation_alias="GITHUB_REPOSITORY",
        description="Target GitHub repo for generated site (e.g. owner/toolnest-site)",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Compute the full list of allowed CORS origins."""
        origins = {self.frontend_origin.strip().rstrip("/")}
        if self.cors_allowed_origins:
            for item in self.cors_allowed_origins.split(","):
                cleaned = item.strip().rstrip("/")
                if cleaned:
                    origins.add(cleaned)
        # Always allow local dev frontend origins in development
        if self.environment in ("development", "testing"):
            origins.update(["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"])
        return sorted(origins)

    def get_sqlalchemy_database_url(self) -> str:
        """
        Return the database URL formatted for SQLAlchemy with psycopg3.
        Raises DatabaseConfigurationError if DATABASE_URL is not set.
        """
        if not self.database_url or not self.database_url.strip():
            raise DatabaseConfigurationError(
                "DATABASE_URL is not configured. Please set the DATABASE_URL environment variable."
            )
        url = self.database_url.strip()
        # Neon and standard connection strings might begin with postgres:// or postgresql://
        # We ensure psycopg3 dialect is used: postgresql+psycopg://
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
