"""Site Settings Model for dynamic limits, switches, and parameters."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import GUID, Base


class SiteSetting(Base):
    """Centralized key-value site configuration table (cached in API)."""

    __tablename__ = "site_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    value: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        comment="JSON-encoded configuration value",
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SiteSetting key={self.key!r}>"
