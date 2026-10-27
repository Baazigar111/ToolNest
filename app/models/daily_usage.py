"""Daily Usage Model for aggregated privacy-safe analytics."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, Base

if TYPE_CHECKING:
    from app.models.tool import Tool


class DailyUsage(Base):
    """Daily aggregated usage and error counters per tool.

    Contains no file names, file contents, or visitor IP addresses.
    """

    __tablename__ = "daily_usage"

    date: Mapped[date] = mapped_column(
        Date,
        primary_key=True,
        nullable=False,
    )
    tool_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("tools.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    uses: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    errors: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    bytes: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )

    tool: Mapped[Tool] = relationship("Tool", back_populates="daily_usages")

    def __repr__(self) -> str:
        return f"<DailyUsage date={self.date} tool_id={self.tool_id} uses={self.uses}>"
