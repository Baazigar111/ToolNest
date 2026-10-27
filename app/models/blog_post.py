"""Blog Post Model and association table for guides and tutorials."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.tool import Tool


class BlogPostTool(Base):
    """Many-to-many association connecting guide articles to relevant tools."""

    __tablename__ = "blog_post_tools"

    blog_post_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("blog_posts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tool_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("tools.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    blog_post: Mapped[BlogPost] = relationship("BlogPost", back_populates="tool_associations")
    tool: Mapped[Tool] = relationship("Tool", back_populates="blog_associations")


class BlogPost(Base, TimestampMixin):
    """Guide articles, tutorials, and informational posts for SEO."""

    __tablename__ = "blog_posts"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    slug: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        nullable=False,
        comment="Article status: draft, published, archived",
    )
    seo_title: Mapped[str | None] = mapped_column(
        String(70),
        nullable=True,
    )
    meta_description: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    tool_associations: Mapped[list[BlogPostTool]] = relationship(
        "BlogPostTool",
        back_populates="blog_post",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<BlogPost slug={self.slug!r} status={self.status!r}>"
