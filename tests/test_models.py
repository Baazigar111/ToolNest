"""Tests for SQLAlchemy model definitions, relations, and constraints."""

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    FAQ,
    AdminUser,
    BlogPost,
    BlogPostTool,
    Category,
    DailyUsage,
    PublishLog,
    SiteSetting,
    Tool,
)


def test_admin_user_creation(db_session: Session):
    """Test creating and querying an AdminUser."""
    user = AdminUser(
        email="admin@toolnest.example",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$fakehash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    saved = db_session.scalar(select(AdminUser).where(AdminUser.email == "admin@toolnest.example"))
    assert saved is not None
    assert saved.email == "admin@toolnest.example"
    assert saved.is_active is True
    assert saved.created_at is not None


def test_admin_user_unique_email(db_session: Session):
    """Test that duplicate email addresses on AdminUser raise IntegrityError."""
    user1 = AdminUser(email="unique@toolnest.example", password_hash="hash1")
    user2 = AdminUser(email="unique@toolnest.example", password_hash="hash2")
    db_session.add(user1)
    db_session.commit()

    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_category_and_tool_relationship(db_session: Session):
    """Test Category and Tool relationship and cascading."""
    cat = Category(name="PDF Tools", slug="pdf", sort_order=1)
    db_session.add(cat)
    db_session.flush()

    tool = Tool(
        name="Merge PDF",
        slug="merge-pdf",
        category_id=cat.id,
        tool_type="pdf",
        endpoint="/api/pdf/merge",
        is_active=True,
    )
    db_session.add(tool)
    db_session.commit()

    loaded_cat = db_session.scalar(select(Category).where(Category.slug == "pdf"))
    assert len(loaded_cat.tools) == 1
    assert loaded_cat.tools[0].name == "Merge PDF"


def test_tool_unique_slug(db_session: Session):
    """Test that duplicate tool slugs are prevented."""
    t1 = Tool(name="Merge 1", slug="merge-pdf", tool_type="pdf")
    t2 = Tool(name="Merge 2", slug="merge-pdf", tool_type="pdf")
    db_session.add(t1)
    db_session.commit()

    db_session.add(t2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_tool_faq_cascade(db_session: Session):
    """Test that deleting a tool cascades and deletes related FAQs."""
    tool = Tool(name="Split PDF", slug="split-pdf", tool_type="pdf")
    db_session.add(tool)
    db_session.flush()

    faq = FAQ(
        tool_id=tool.id,
        question="How do I split pages?",
        answer="Select page ranges and click Split.",
        sort_order=1,
    )
    db_session.add(faq)
    db_session.commit()

    assert db_session.scalar(select(FAQ).where(FAQ.tool_id == tool.id)) is not None

    db_session.delete(tool)
    db_session.commit()

    assert db_session.scalar(select(FAQ).where(FAQ.tool_id == tool.id)) is None


def test_blog_post_and_tools_association(db_session: Session):
    """Test association table between BlogPost and Tools."""
    tool1 = Tool(name="Word Counter", slug="word-counter", tool_type="browser")
    tool2 = Tool(name="Case Converter", slug="case-converter", tool_type="browser")
    db_session.add_all([tool1, tool2])
    db_session.flush()

    post = BlogPost(
        slug="how-to-format-text",
        title="How to Format Text Online",
        body="Detailed guide content...",
        status="published",
    )
    db_session.add(post)
    db_session.flush()

    assoc1 = BlogPostTool(blog_post_id=post.id, tool_id=tool1.id, sort_order=1)
    assoc2 = BlogPostTool(blog_post_id=post.id, tool_id=tool2.id, sort_order=2)
    db_session.add_all([assoc1, assoc2])
    db_session.commit()

    loaded_post = db_session.scalar(select(BlogPost).where(BlogPost.slug == "how-to-format-text"))
    assert len(loaded_post.tool_associations) == 2


def test_site_setting_key_unique(db_session: Session):
    """Test SiteSetting key uniqueness and JSON value storage."""
    s1 = SiteSetting(key="gst_rates", value=[0, 5, 18, 40])
    db_session.add(s1)
    db_session.commit()

    s2 = SiteSetting(key="gst_rates", value=[5, 12, 18, 28])
    db_session.add(s2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_daily_usage_composite_key(db_session: Session):
    """Test DailyUsage composite key on (date, tool_id)."""
    tool = Tool(name="QR Code Generator", slug="qr-code-generator", tool_type="qr")
    db_session.add(tool)
    db_session.flush()

    today = date(2026, 10, 27)
    usage1 = DailyUsage(date=today, tool_id=tool.id, uses=10, errors=1, bytes=10240)
    db_session.add(usage1)
    db_session.commit()
    db_session.expunge(usage1)

    usage2 = DailyUsage(date=today, tool_id=tool.id, uses=5, errors=0, bytes=5120)
    db_session.add(usage2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_publish_log_creation(db_session: Session):
    """Test creating and reading a PublishLog entry."""
    log = PublishLog(
        status="success",
        changed_files=["index.html", "sitemap.xml"],
        error_text=None,
    )
    db_session.add(log)
    db_session.commit()

    saved = db_session.scalar(select(PublishLog).where(PublishLog.id == log.id))
    assert saved is not None
    assert saved.status == "success"
    assert "index.html" in saved.changed_files
