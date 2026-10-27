"""Tests for SiteValidator pre-deployment checks."""

import tempfile
from pathlib import Path

from site_builder.validator import SiteValidator


def test_validator_detects_missing_required_file():
    """Verify validator fails if index.html is missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        validator = SiteValidator(dir_path)
        res = validator.validate()
        assert res.is_valid is False
        assert any("index.html" in err for err in res.errors)


def test_validator_detects_multiple_h1_tags():
    """Verify validator flags violations of the single-H1 rule."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        # Create minimal structure
        (dir_path / "about").mkdir(parents=True)
        bad_html = "<html><head><title>Test</title></head><body><h1>One</h1><h1>Two</h1></body></html>"
        (dir_path / "about" / "index.html").write_text(bad_html, encoding="utf-8")

        validator = SiteValidator(dir_path)
        res = validator.validate()
        assert res.is_valid is False
        assert any("Multiple <h1>" in err for err in res.errors)


def test_validator_detects_secret_leak():
    """Verify validator flags any accidental leakage of database credentials."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        (dir_path / "index.html").write_text(
            "<html><head><title>Home</title></head><body><h1>ToolNest</h1><p>DB: postgresql://user:pass@ep-demo.neon.tech/db</p></body></html>",
            encoding="utf-8",
        )

        validator = SiteValidator(dir_path)
        res = validator.validate()
        assert res.is_valid is False
        assert any("POTENTIAL SECRET LEAK" in err for err in res.errors)
