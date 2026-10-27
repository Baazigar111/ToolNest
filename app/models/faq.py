"""FAQ Model for tool-specific frequently asked questions."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tool import Tool


class FAQ(Base, TimestampMixin):
    """Frequently Asked Questions displayed on individual tool pages."""

    __tablename__ = "faqs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    tool_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("tools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    tool: Mapped[Tool] = relationship("Tool", back_populates="faqs")

    def __repr__(self) -> str:
        return f"<FAQ tool_id={self.tool_id} question={self.question[:30]!r}>"
