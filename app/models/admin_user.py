"""Admin User Model for authentication and administrative access."""

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, Base, TimestampMixin


class AdminUser(Base, TimestampMixin):
    """Administrator account table for SQLAdmin and management tasks."""

    __tablename__ = "admin_users"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    publish_logs = relationship("PublishLog", back_populates="admin_user")

    def __repr__(self) -> str:
        return f"<AdminUser email={self.email!r} is_active={self.is_active}>"
