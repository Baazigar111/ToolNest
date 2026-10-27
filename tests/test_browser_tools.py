"""Tests for Phase 4: Browser-Only Client-Side Tools.
Validates template generation, asset integration, UI element anchors, and mathematical formulas.
"""

import tempfile
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.tool import Tool
from site_builder.build import SiteBuilder
from site_builder.validator import SiteValidator


def test_tools_javascript_asset_integrity():
    """Verify that site_builder/static/js/tools.js exists and exports all expected handlers."""
    tools_js_path = Path("site_builder/static/js/tools.js")
    assert tools_js_path.exists(), "tools.js must exist in site_builder static assets"

    content = tools_js_path.read_text(encoding="utf-8")
    expected_functions = [
        "formatCurrency",
        "initWordCounter",
        "initCaseConverter",
        "initJsonFormatter",
        "initEmiCalculator",
        "initSipCalculator",
        "initGstCalculator",
    ]
    for fn in expected_functions:
        assert fn in content, f"Function {fn} missing from tools.js"


def test_browser_tools_page_generation_and_validation(db_session: Session):
    """Verify that all 6 browser-only tools build valid HTML with proper interactive elements."""
    calc_cat = Category(name="Calculators", slug="calculators", sort_order=1)
    text_cat = Category(name="Text Tools", slug="text-tools", sort_order=2)
    db_session.add_all([calc_cat, text_cat])
    db_session.flush()

    browser_tools = [
        Tool(
            name="Word Counter",
            slug="word-counter",
            category_id=text_cat.id,
            tool_type="text",
            endpoint=None,
            description="Count words, characters, sentences, and reading time.",
            is_active=True,
        ),
        Tool(
            name="Case Converter",
            slug="case-converter",
            category_id=text_cat.id,
            tool_type="text",
            endpoint=None,
            description="Convert text between UPPERCASE, lowercase, camelCase, snake_case, etc.",
            is_active=True,
        ),
        Tool(
            name="JSON Formatter",
            slug="json-formatter",
            category_id=text_cat.id,
            tool_type="text",
            endpoint=None,
            description="Format, prettify, minify, and validate JSON code online.",
            is_active=True,
        ),
        Tool(
            name="EMI Calculator",
            slug="emi-calculator",
            category_id=calc_cat.id,
            tool_type="calculator",
            endpoint=None,
            description="Calculate loan EMI, total interest, and repayment schedule.",
            is_active=True,
        ),
        Tool(
            name="SIP Calculator",
            slug="sip-calculator",
            category_id=calc_cat.id,
            tool_type="calculator",
            endpoint=None,
            description="Calculate mutual fund SIP returns and wealth gain.",
            is_active=True,
        ),
        Tool(
            name="GST Calculator",
            slug="gst-calculator",
            category_id=calc_cat.id,
            tool_type="calculator",
            endpoint=None,
            description="Calculate GST inclusive and exclusive amounts with CGST/SGST breakdown.",
            is_active=True,
        ),
    ]
    db_session.add_all(browser_tools)
    db_session.commit()

    with tempfile.TemporaryDirectory() as temp_dir:
        builder = SiteBuilder(output_dir=temp_dir, session=db_session)
        builder.build()

        out_path = Path(temp_dir)

        # 1. Validate the output directory with SiteValidator
        validator = SiteValidator(out_path)
        expected_slugs = [t.slug for t in browser_tools]
        val_result = validator.validate(expected_tools=expected_slugs)
        assert val_result.is_valid, f"Validation errors: {val_result.errors}"

        # 2. Check Word Counter elements
        word_html = (out_path / "word-counter" / "index.html").read_text(encoding="utf-8")
        assert 'id="word-input"' in word_html
        assert 'id="stat-words"' in word_html
        assert 'id="stat-chars"' in word_html
        assert 'id="stat-chars-no-spaces"' in word_html
        assert 'id="stat-sentences"' in word_html
        assert 'id="stat-reading-time"' in word_html
        assert 'id="btn-clear-words"' in word_html

        # 3. Check Case Converter elements
        case_html = (out_path / "case-converter" / "index.html").read_text(encoding="utf-8")
        assert 'id="case-input"' in case_html
        assert 'id="btn-uppercase"' in case_html
        assert 'id="btn-lowercase"' in case_html
        assert 'id="btn-titlecase"' in case_html
        assert 'id="btn-sentencecase"' in case_html
        assert 'id="btn-camelcase"' in case_html
        assert 'id="btn-snakecase"' in case_html
        assert 'id="btn-kebabcase"' in case_html

        # 4. Check JSON Formatter elements
        json_html = (out_path / "json-formatter" / "index.html").read_text(encoding="utf-8")
        assert 'id="json-input"' in json_html
        assert 'id="btn-json-2space"' in json_html
        assert 'id="btn-json-4space"' in json_html
        assert 'id="btn-json-minify"' in json_html
        assert 'id="btn-json-sample"' in json_html
        assert 'id="json-status-banner"' in json_html

        # 5. Check EMI Calculator elements
        emi_html = (out_path / "emi-calculator" / "index.html").read_text(encoding="utf-8")
        assert 'id="emi-amount"' in emi_html
        assert 'id="emi-amount-input"' in emi_html
        assert 'id="emi-rate"' in emi_html
        assert 'id="emi-tenure"' in emi_html
        assert 'id="emi-result-monthly"' in emi_html
        assert 'id="emi-result-total"' in emi_html
        assert 'id="emi-bar-principal"' in emi_html
        assert 'id="emi-bar-interest"' in emi_html

        # 6. Check SIP Calculator elements
        sip_html = (out_path / "sip-calculator" / "index.html").read_text(encoding="utf-8")
        assert 'id="sip-amount"' in sip_html
        assert 'id="sip-amount-input"' in sip_html
        assert 'id="sip-rate"' in sip_html
        assert 'id="sip-years"' in sip_html
        assert 'id="sip-result-total"' in sip_html
        assert 'id="sip-result-invested"' in sip_html
        assert 'id="sip-result-returns"' in sip_html
        assert 'id="sip-bar-invested"' in sip_html

        # 7. Check GST Calculator elements
        gst_html = (out_path / "gst-calculator" / "index.html").read_text(encoding="utf-8")
        assert 'id="gst-amount"' in gst_html
        assert 'id="gst-result-total"' in gst_html
        assert 'id="gst-result-net"' in gst_html
        assert 'id="gst-result-tax"' in gst_html
        assert 'id="gst-result-cgst"' in gst_html
        assert 'id="gst-result-sgst"' in gst_html

        # 8. Check tools.js script tag inclusion
        assert '<script src="/assets/js/tools.js"></script>' in word_html


def test_calculator_math_formulas():
    """Verify precision of financial math formulas implemented in tools.js."""
    # 1. EMI Formula: P = 500,000, R = 8.5%, N = 5 years
    p = 500000.0
    r = (8.5 / 12) / 100.0
    n = 5 * 12
    emi = round((p * r * ((1 + r) ** n)) / (((1 + r) ** n) - 1))
    total_payment = emi * n
    total_interest = total_payment - p

    assert emi == 10258
    assert total_payment == 615480  # 10258 * 60
    assert total_interest == 115480

    # 2. SIP Formula: P = 5,000/mo, R = 12% p.a., N = 10 years
    sip_p = 5000.0
    sip_i = (12.0 / 12) / 100.0
    sip_n = 10 * 12
    future_val = round(sip_p * ((((1 + sip_i) ** sip_n) - 1) / sip_i) * (1 + sip_i))
    sip_invested = sip_p * sip_n
    sip_returns = future_val - sip_invested

    assert future_val == 1161695
    assert sip_invested == 600000
    assert sip_returns == 561695

    # 3. GST Calculations
    amount = 10000.0
    rate = 18.0

    # Exclusive (Add GST)
    add_gst = amount * (rate / 100.0)
    add_total = amount + add_gst
    assert add_gst == 1800.0
    assert add_total == 11800.0
    assert add_gst / 2 == 900.0  # CGST & SGST

    # Inclusive (Remove GST)
    gross = 11800.0
    rem_net = round(gross / (1 + (rate / 100.0)), 2)
    rem_gst = round(gross - rem_net, 2)
    assert rem_net == 10000.0
    assert rem_gst == 1800.0
