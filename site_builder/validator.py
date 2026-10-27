"""Validator for generated static site files prior to GitHub publishing."""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NamedTuple


class ValidationResult(NamedTuple):
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    total_files_checked: int


class SiteValidator:
    """Validates generated HTML, assets, sitemap, and secrets in output directory."""

    SECRET_PATTERNS = [
        re.compile(r"postgres(ql)?:\/\/[^\"\s]+", re.IGNORECASE),
        re.compile(r"ADMIN_SECRET_KEY", re.IGNORECASE),
        re.compile(r"ghp_[a-zA-Z0-9]{20,}", re.IGNORECASE),
        re.compile(r"password_hash", re.IGNORECASE),
    ]

    def __init__(self, site_dir: Path | str) -> None:
        self.site_dir = Path(site_dir)

    def validate(self, expected_tools: list[str] | None = None) -> ValidationResult:
        """Run all validation checks on the output directory."""
        errors: list[str] = []
        warnings: list[str] = []
        total_files = 0

        if not self.site_dir.exists():
            return ValidationResult(False, [f"Output directory '{self.site_dir}' does not exist."], [], 0)

        # 1. Essential files existence check
        required_files = [
            "index.html",
            "sitemap.xml",
            "robots.txt",
            "about/index.html",
            "privacy/index.html",
            "terms/index.html",
            "contact/index.html",
            "assets/css/style.css",
            "assets/js/main.js",
            "assets/js/theme.js",
            "assets/js/api.js",
            "assets/js/tools.js",
        ]

        for rel in required_files:
            file_path = self.site_dir / rel
            if not file_path.exists() or file_path.stat().st_size == 0:
                errors.append(f"Required file missing or empty: {rel}")

        # 2. Expected tool pages check
        if expected_tools:
            for slug in expected_tools:
                tool_file = self.site_dir / slug / "index.html"
                if not tool_file.exists():
                    errors.append(f"Tool page missing: {slug}/index.html")

        # 3. HTML Content Validation & Secrets Scanning
        html_files = list(self.site_dir.rglob("*.html"))
        total_files += len(html_files)

        for html_path in html_files:
            content = html_path.read_text(encoding="utf-8")
            rel_name = html_path.relative_to(self.site_dir).as_posix()

            # Check single H1 rule
            h1_count = len(re.findall(r"<h1\b[^>]*>", content, re.IGNORECASE))
            if h1_count == 0:
                errors.append(f"Missing <h1> tag in {rel_name}")
            elif h1_count > 1:
                errors.append(f"Multiple <h1> tags ({h1_count}) found in {rel_name}")

            # Check Title
            if not re.search(r"<title>[^<]+<\/title>", content, re.IGNORECASE):
                errors.append(f"Missing or empty <title> tag in {rel_name}")

            # Check Meta Description
            if not re.search(r'<meta\s+name=["\']description["\']\s+content=["\'][^"\']+["\']', content, re.IGNORECASE):
                warnings.append(f"Missing meta description in {rel_name}")

            # Check Canonical
            if not re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\'][^"\']+["\']', content, re.IGNORECASE):
                warnings.append(f"Missing canonical link in {rel_name}")

            # Scan for leaked secrets
            for pattern in self.SECRET_PATTERNS:
                if pattern.search(content):
                    errors.append(f"POTENTIAL SECRET LEAK detected in {rel_name} matching {pattern.pattern}")

        # 4. Sitemap XML Validation
        sitemap_path = self.site_dir / "sitemap.xml"
        if sitemap_path.exists():
            total_files += 1
            try:
                tree = ET.parse(sitemap_path)
                root = tree.getroot()
                urls = root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url")
                if len(urls) < 5:
                    warnings.append(f"Sitemap has only {len(urls)} URLs. Expected more entries.")
            except Exception as e:
                errors.append(f"Malformed sitemap.xml: {e}")

        # 5. Robots.txt Validation
        robots_path = self.site_dir / "robots.txt"
        if robots_path.exists():
            total_files += 1
            robots_content = robots_path.read_text(encoding="utf-8")
            if "Sitemap:" not in robots_content:
                warnings.append("robots.txt does not declare Sitemap: directive")

        # Check total file count & size limit per Cloudflare Pages (20,000 files, 25MB per file)
        for root, _, files in os.walk(self.site_dir):
            for f in files:
                f_path = Path(root) / f
                if f_path.stat().st_size > 25 * 1024 * 1024:
                    errors.append(f"File exceeds Cloudflare Pages 25MB limit: {f_path.relative_to(self.site_dir)}")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, total_files)
