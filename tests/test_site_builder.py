"""Tests for static site generation with Jinja2."""

import tempfile
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.tool import Tool
from site_builder.build import SiteBuilder


def test_site_builder_renders_all_pages(db_session: Session):
    """Verify that SiteBuilder outputs home, tool, category, and policy pages."""
    # Seed a category and two active tools
    cat = Category(name="PDF Tools", slug="pdf", sort_order=1)
    db_session.add(cat)
    db_session.flush()

    tool1 = Tool(
        name="Merge PDF",
        slug="merge-pdf",
        category_id=cat.id,
        tool_type="pdf",
        endpoint="/api/pdf/merge",
        description="Merge multiple PDFs into one.",
        how_to_steps=["Upload files", "Reorder", "Merge", "Download"],
        is_active=True,
    )
    tool2 = Tool(
        name="Compress PDF",
        slug="compress-pdf",
        category_id=cat.id,
        tool_type="pdf",
        endpoint="/api/pdf/compress",
        description="Compress PDF to smaller size.",
        how_to_steps=["Upload PDF", "Select level", "Compress", "Download"],
        is_active=True,
    )
    db_session.add_all([tool1, tool2])
    db_session.commit()

    with tempfile.TemporaryDirectory() as temp_dir:
        builder = SiteBuilder(output_dir=temp_dir, session=db_session)
        builder.build()

        out_path = Path(temp_dir)
        # Check core files exist
        assert (out_path / "index.html").exists()
        assert (out_path / "merge-pdf" / "index.html").exists()
        assert (out_path / "compress-pdf" / "index.html").exists()
        assert (out_path / "category" / "pdf" / "index.html").exists()
        assert (out_path / "blog" / "index.html").exists()
        assert (out_path / "about" / "index.html").exists()
        assert (out_path / "privacy" / "index.html").exists()
        assert (out_path / "terms" / "index.html").exists()
        assert (out_path / "contact" / "index.html").exists()
        assert (out_path / "sitemap.xml").exists()
        assert (out_path / "robots.txt").exists()

        # Check assets exist
        assert (out_path / "assets" / "css" / "style.css").exists()
        assert (out_path / "assets" / "js" / "main.js").exists()

        # Check content structure on tool page
        tool_content = (out_path / "merge-pdf" / "index.html").read_text(encoding="utf-8")
        assert '<h1 class="tool-page-h1">Merge PDF</h1>' in tool_content
        assert "How to Use Merge PDF" in tool_content
        assert "SoftwareApplication" in tool_content
        assert '<link rel="canonical"' in tool_content

        # Check sitemap content
        sitemap_content = (out_path / "sitemap.xml").read_text(encoding="utf-8")
        assert "/merge-pdf</loc>" in sitemap_content
        assert "/compress-pdf</loc>" in sitemap_content
        assert "/category/pdf</loc>" in sitemap_content
