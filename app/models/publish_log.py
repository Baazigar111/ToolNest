"""Publish Log Model for tracking static site generation and GitHub commits."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, Base


class PublishLog(Base):
    """Audit log for static site builds and GitHub publishing actions."""

    __tablename__ = "publish_log"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    admin_user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Publish status: pending, success, failed",
    )
    changed_files: Mapped[Any | None] = mapped_column(
        JSON,
        nullable=True,
        comment="List or count summary of changed files deployed",
    )
    error_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed sanitized error description if build or commit failed",
    )

    admin_user = relationship("AdminUser", back_populates="publish_logs")

    def __repr__(self) -> str:
        return f"<PublishLog id={self.id} status={self.status!r} created_at={self.created_at}>"
