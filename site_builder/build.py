"""Static Site Generator for ToolNest using Jinja2 and PostgreSQL."""

import os
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session_factory
from app.models.blog_post import BlogPost
from app.models.category import Category
from app.models.site_setting import SiteSetting
from app.models.tool import Tool

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"


class SiteBuilder:
    """Renders static HTML, assets, sitemap.xml, and robots.txt from database models."""

    def __init__(self, output_dir: Path | str, session: Session | None = None) -> None:
        self.output_dir = Path(output_dir)
        self.session = session
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _get_context_data(self) -> dict[str, Any]:
        """Fetch all necessary data from database for static page generation."""
        settings = get_settings()
        site_url = settings.frontend_origin.rstrip("/")
        api_base_url = settings.api_base_url.rstrip("/")

        ads_enabled = False
        gst_rates = [0, 5, 18, 40]

        categories: list[Category] = []
        tools: list[Tool] = []
        posts: list[BlogPost] = []

        if self.session is not None:
            categories = list(self.session.scalars(select(Category).order_by(Category.sort_order)).all())
            tools = list(self.session.scalars(select(Tool).where(Tool.is_active.is_(True)).order_by(Tool.name)).all())
            posts = list(self.session.scalars(select(BlogPost).where(BlogPost.status == "published").order_by(BlogPost.published_at.desc())).all())

            # Read site settings overrides
            ads_setting = self.session.scalar(select(SiteSetting).where(SiteSetting.key == "ads_enabled"))
            if ads_setting:
                ads_enabled = bool(ads_setting.value)

            gst_setting = self.session.scalar(select(SiteSetting).where(SiteSetting.key == "gst_rates"))
            if gst_setting and isinstance(gst_setting.value, list):
                gst_rates = gst_setting.value

        return {
            "site_url": site_url,
            "api_base_url": api_base_url,
            "ads_enabled": ads_enabled,
            "gst_rates": gst_rates,
            "categories": categories,
            "tools": tools,
            "posts": posts,
            "current_year": datetime.now().year,
            "build_date": date.today().isoformat(),
        }

    def _write_file(self, rel_path: str, content: str) -> Path:
        """Write content to the specified path within the output directory."""
        target_path = self.output_dir / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return target_path

    def build(self) -> list[Path]:
        """Execute full static site generation, returning list of all written files."""
        generated_files: list[Path] = []
        context = self._get_context_data()

        # 1. Clean or create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 2. Copy static assets (css, js, images) to assets/
        assets_dest = self.output_dir / "assets"
        if assets_dest.exists():
            shutil.rmtree(assets_dest)
        if STATIC_DIR.exists():
            shutil.copytree(STATIC_DIR, assets_dest)
            for root, _, files in os.walk(assets_dest):
                for f in files:
                    generated_files.append(Path(root) / f)

        # 3. Render Homepage
        home_tpl = self.env.get_template("home.html")
        home_html = home_tpl.render(
            **context,
            page_type="home",
            seo_title="ToolNest — Free Online PDF, Image, Text & Finance Tools",
            meta_description="Everyday online tools for PDF merging, image compression, QR generation, EMI calculation, and text formatting. Free with no registration.",
            canonical_path="/",
        )
        generated_files.append(self._write_file("index.html", home_html))

        # 4. Render All Tool Pages (Clean URLs: /{slug}/index.html)
        tool_tpl = self.env.get_template("tool.html")
        all_tools = context["tools"]

        for tool in all_tools:
            # Related tools: select up to 3 tools in same category, or other active tools
            related = [t for t in all_tools if t.id != tool.id and t.category_id == tool.category_id][:3]
            if len(related) < 3:
                related.extend([t for t in all_tools if t.id != tool.id and t not in related][: 3 - len(related)])

            tool_html = tool_tpl.render(
                **context,
                tool=tool,
                related_tools=related,
                seo_title=tool.seo_title or f"{tool.name} Online Free - ToolNest",
                meta_description=tool.meta_description or f"Use {tool.name} for free online on ToolNest.",
                canonical_path=f"/{tool.slug}",
            )
            generated_files.append(self._write_file(f"{tool.slug}/index.html", tool_html))

        # 5. Render Category Pages (/category/{slug}/index.html)
        cat_tpl = self.env.get_template("category.html")
        for cat in context["categories"]:
            cat_html = cat_tpl.render(
                **context,
                category=cat,
                current_category=cat,
                seo_title=f"{cat.name} — Free Online Tools - ToolNest",
                meta_description=f"Free online tools for {cat.name.lower()}. {cat.description or ''}",
                canonical_path=f"/category/{cat.slug}",
            )
            generated_files.append(self._write_file(f"category/{cat.slug}/index.html", cat_html))

        # 6. Render Blog Index & Article Pages
        blog_list_tpl = self.env.get_template("blog_list.html")
        blog_html = blog_list_tpl.render(
            **context,
            page_type="blog",
            seo_title="Guides & Productivity Tutorials - ToolNest",
            meta_description="Helpful guides on managing PDF files, photo compression limits, and financial calculations.",
            canonical_path="/blog",
        )
        generated_files.append(self._write_file("blog/index.html", blog_html))

        blog_post_tpl = self.env.get_template("blog_post.html")
        for post in context["posts"]:
            post_html = blog_post_tpl.render(
                **context,
                post=post,
                page_type="blog",
                seo_title=post.seo_title or f"{post.title} - ToolNest",
                meta_description=post.meta_description or post.description,
                canonical_path=f"/blog/{post.slug}",
            )
            generated_files.append(self._write_file(f"blog/{post.slug}/index.html", post_html))

        # 7. Render Policy Pages
        for policy in ["about", "privacy", "terms", "contact"]:
            policy_tpl = self.env.get_template(f"{policy}.html")
            policy_title = f"{policy.capitalize()} Us - ToolNest" if policy in ["about", "contact"] else f"{policy.capitalize()} Policy - ToolNest"
            policy_html = policy_tpl.render(
                **context,
                seo_title=policy_title,
                meta_description=f"ToolNest {policy} and user information.",
                canonical_path=f"/{policy}",
            )
            generated_files.append(self._write_file(f"{policy}/index.html", policy_html))

        # 8. Render sitemap.xml & robots.txt
        sitemap_tpl = self.env.get_template("sitemap.xml")
        sitemap_xml = sitemap_tpl.render(**context)
        generated_files.append(self._write_file("sitemap.xml", sitemap_xml))

        robots_tpl = self.env.get_template("robots.txt")
        robots_txt = robots_tpl.render(**context)
        generated_files.append(self._write_file("robots.txt", robots_txt))

        return generated_files


def run_build(output_dir: Path | str = "dist") -> list[Path]:
    """CLI / Programmatic entry point to execute build using current database connection."""
    session = None
    try:
        session_factory = get_session_factory()
        session = session_factory()
    except Exception:
        # Build runs with empty/default context if database is unconfigured
        pass

    try:
        builder = SiteBuilder(output_dir=output_dir, session=session)
        files = builder.build()
        print(f"Build complete. Generated {len(files)} files in {output_dir}")
        return files
    finally:
        if session:
            session.close()


if __name__ == "__main__":
    run_build()
