"""SQLAdmin application setup and view registration."""

from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from app.admin.auth import AdminAuth
from app.admin.views import (
    AdminUserAdmin,
    BlogPostAdmin,
    CategoryAdmin,
    DailyUsageAdmin,
    FAQAdmin,
    PublishLogAdmin,
    SiteSettingAdmin,
    ToolAdmin,
)
from app.config import get_settings
from app.db import get_engine, get_session_factory


def setup_admin(
    app: FastAPI,
    engine: Engine | None = None,
    session_factory=None,
) -> Admin | None:
    """
    Configure and attach SQLAdmin to the FastAPI application.
    If engine is not explicitly provided, attempts to obtain it from get_engine().
    If database is unconfigured, returns None gracefully without crashing.
    """
    settings = get_settings()

    if engine is None:
        try:
            engine = get_engine()
        except Exception:
            # Database is not yet configured, skip admin initialization
            return None

    if session_factory is None and engine is not None:
        session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    auth_backend = AdminAuth(
        secret_key=settings.admin_secret_key,
        session_factory=session_factory or get_session_factory(),
    )

    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=auth_backend,
        title="ToolNest Admin",
        base_url="/admin",
        logo_url=None,
    )

    # Register Model Views
    admin.add_view(ToolAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(FAQAdmin)
    admin.add_view(BlogPostAdmin)
    admin.add_view(SiteSettingAdmin)
    admin.add_view(DailyUsageAdmin)
    admin.add_view(PublishLogAdmin)
    admin.add_view(AdminUserAdmin)

    return admin
