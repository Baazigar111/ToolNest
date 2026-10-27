"""ToolNest FastAPI Application Entry Point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.admin.setup import setup_admin
from app.config import get_settings
from app.errors import register_error_handlers
from app.routers import (
    health_router,
    image_router,
    pdf_router,
    publish_router,
    qr_router,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing standard web security headers on all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and graceful shutdown."""
    # Startup actions
    yield
    # Shutdown actions (e.g., disposing cached database engine)
    from app.db import reset_engine
    reset_engine()


def create_app(engine=None) -> FastAPI:
    """FastAPI application factory for ToolNest."""
    settings = get_settings()

    app = FastAPI(
        title="ToolNest API",
        description="Backend API and file processing service for ToolNest free online tools.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Security Headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Signed Session Middleware for Admin Authentication
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.admin_secret_key,
        session_cookie=settings.session_cookie_name,
        https_only=settings.cookie_secure,
        same_site="lax",
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Standardize JSON Error Contracts
    register_error_handlers(app)

    # Mount Core Routers
    app.include_router(health_router)
    app.include_router(publish_router)
    app.include_router(qr_router)
    app.include_router(pdf_router)
    app.include_router(image_router)

    # Mount SQLAdmin Panel
    setup_admin(app, engine=engine)

    return app


app = create_app()
