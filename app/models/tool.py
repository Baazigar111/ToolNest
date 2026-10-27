"""Tool Model for metadata, configuration, and SEO fields."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import GUID, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.blog_post import BlogPostTool
    from app.models.category import Category
    from app.models.daily_usage import DailyUsage
    from app.models.faq import FAQ


class Tool(Base, TimestampMixin):
    """Tool metadata and public page content table."""

    __tablename__ = "tools"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    tool_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Tool category type: pdf, image, qr, browser, calculator",
    )
    endpoint: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Backend API endpoint if applicable (e.g. /api/pdf/merge)",
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="One-sentence short description",
    )
    intro_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Short introductory paragraph",
    )
    how_to_steps: Mapped[Any | None] = mapped_column(
        JSON,
        nullable=True,
        comment="List of step strings for how to use the tool",
    )
    long_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="300+ word detailed guide and content for SEO",
    )
    seo_title: Mapped[str | None] = mapped_column(
        String(70),
        nullable=True,
        comment="Unique SEO title up to 60-70 characters",
    )
    meta_description: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
        comment="Unique meta description up to 155-160 characters",
    )
    canonical_path: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Canonical path, e.g. /merge-pdf",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Kill-switch flag to instantly disable a tool without static redeployment",
    )

    category: Mapped[Category | None] = relationship("Category", back_populates="tools")
    faqs: Mapped[list[FAQ]] = relationship("FAQ", back_populates="tool", cascade="all, delete-orphan")
    daily_usages: Mapped[list[DailyUsage]] = relationship("DailyUsage", back_populates="tool", cascade="all, delete-orphan")
    blog_associations: Mapped[list[BlogPostTool]] = relationship("BlogPostTool", back_populates="tool", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tool slug={self.slug!r} name={self.name!r} is_active={self.is_active}>"
