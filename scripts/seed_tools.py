"""Database seed script for ToolNest categories, 15 core tools, and site settings."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config import DatabaseConfigurationError
from app.db import get_session_factory
from app.models import Category, SiteSetting, Tool

CATEGORIES = [
    {"slug": "pdf", "name": "PDF Tools", "description": "Merge, split, compress, and convert PDF documents easily.", "sort_order": 1},
    {"slug": "image", "name": "Image Tools", "description": "Compress, resize, convert image formats, and create PDFs from photos.", "sort_order": 2},
    {"slug": "qr", "name": "QR Codes", "description": "Generate custom QR codes for URLs, UPI payments, Wi-Fi, and text.", "sort_order": 3},
    {"slug": "text", "name": "Text Utilities", "description": "Fast in-browser word counting and case conversions.", "sort_order": 4},
    {"slug": "developer", "name": "Developer Tools", "description": "Private in-browser JSON formatter and validator.", "sort_order": 5},
    {"slug": "finance", "name": "Financial Calculators", "description": "Accurate EMI, SIP future value, and Indian GST calculators.", "sort_order": 6},
]

TOOLS = [
    # PDF Tools
    {
        "category_slug": "pdf",
        "slug": "merge-pdf",
        "name": "Merge PDF",
        "tool_type": "pdf",
        "endpoint": "/api/pdf/merge",
        "description": "Combine multiple PDF files into one single document in seconds.",
        "seo_title": "Merge PDF Files Online Free - ToolNest",
        "meta_description": "Combine 2 to 5 PDF documents into a single organized file for free without signup.",
        "canonical_path": "/merge-pdf",
        "how_to_steps": ["Select 2 to 5 PDF files", "Reorder files if desired", "Click Merge PDF", "Download your merged PDF"],
    },
    {
        "category_slug": "pdf",
        "slug": "split-pdf",
        "name": "Split PDF",
        "tool_type": "pdf",
        "endpoint": "/api/pdf/split",
        "description": "Extract specific pages or page ranges from a PDF document.",
        "seo_title": "Split PDF Pages Online Free - ToolNest",
        "meta_description": "Extract page ranges or separate all pages from your PDF file quickly and securely.",
        "canonical_path": "/split-pdf",
        "how_to_steps": ["Upload your PDF document", "Specify page ranges or select split mode", "Click Split PDF", "Download individual pages or ZIP"],
    },
    {
        "category_slug": "pdf",
        "slug": "compress-pdf",
        "name": "Compress PDF",
        "tool_type": "pdf",
        "endpoint": "/api/pdf/compress",
        "description": "Reduce PDF file size while maintaining sharp text and image clarity.",
        "seo_title": "Compress PDF Online to 100KB Free - ToolNest",
        "meta_description": "Compress PDF files for government portal uploads, job applications, and emails.",
        "canonical_path": "/compress-pdf",
        "how_to_steps": ["Upload your PDF file", "Choose compression level (low, medium, high)", "Click Compress PDF", "Download smaller PDF with before/after stats"],
    },
    {
        "category_slug": "pdf",
        "slug": "pdf-to-image",
        "name": "PDF to Image",
        "tool_type": "pdf",
        "endpoint": "/api/pdf/to-image",
        "description": "Convert PDF pages into high-resolution PNG or JPG images.",
        "seo_title": "Convert PDF to JPG or PNG Online Free - ToolNest",
        "meta_description": "Convert PDF pages up to 15 pages into clean PNG or JPG images packaged as a ZIP.",
        "canonical_path": "/pdf-to-image",
        "how_to_steps": ["Upload your PDF", "Choose output format (PNG or JPG) and DPI", "Click Convert to Image", "Download ZIP file"],
    },
    # Image Tools
    {
        "category_slug": "image",
        "slug": "compress-image",
        "name": "Compress Image",
        "tool_type": "image",
        "endpoint": "/api/image/compress",
        "description": "Compress JPG, PNG, and WebP images to custom quality or target KB.",
        "seo_title": "Compress Image to 50KB or 100KB Online - ToolNest",
        "meta_description": "Shrink photos to exact portal limits like 50KB or 100KB without losing clarity.",
        "canonical_path": "/compress-image",
        "how_to_steps": ["Upload photo or graphic", "Set quality percentage or target KB limit", "Click Compress Image", "Download optimized image"],
    },
    {
        "category_slug": "image",
        "slug": "resize-image",
        "name": "Resize Image",
        "tool_type": "image",
        "endpoint": "/api/image/resize",
        "description": "Change image pixel dimensions or percentage while locking aspect ratio.",
        "seo_title": "Resize Image Dimensions Online Free - ToolNest",
        "meta_description": "Resize photos by pixels or percentage with aspect ratio lock up to 6000px.",
        "canonical_path": "/resize-image",
        "how_to_steps": ["Upload image", "Enter new width and height or percentage", "Toggle aspect ratio lock", "Download resized image"],
    },
    {
        "category_slug": "image",
        "slug": "convert-image",
        "name": "Convert Image",
        "tool_type": "image",
        "endpoint": "/api/image/convert",
        "description": "Convert images between JPG, PNG, and WebP formats instantly.",
        "seo_title": "Convert Image to PNG, JPG, WebP Free - ToolNest",
        "meta_description": "Convert image formats with transparency preservation or clean white backgrounds.",
        "canonical_path": "/convert-image",
        "how_to_steps": ["Upload your image", "Select target format (JPG, PNG, WebP)", "Click Convert", "Download converted image"],
    },
    {
        "category_slug": "image",
        "slug": "image-to-pdf",
        "name": "Image to PDF",
        "tool_type": "image",
        "endpoint": "/api/image/to-pdf",
        "description": "Combine 1 to 5 images into a single professional PDF document.",
        "seo_title": "Convert JPG and PNG Photos to PDF Online - ToolNest",
        "meta_description": "Convert JPG, PNG, or WebP pictures into a clean PDF document with custom margins and page sizes.",
        "canonical_path": "/image-to-pdf",
        "how_to_steps": ["Upload 1 to 5 images", "Select page size, orientation, and margins", "Click Create PDF", "Download output PDF"],
    },
    # QR Codes
    {
        "category_slug": "qr",
        "slug": "qr-code-generator",
        "name": "QR Code Generator",
        "tool_type": "qr",
        "endpoint": "/api/qr",
        "description": "Create customizable QR codes for links, Wi-Fi, WhatsApp, and UPI payments.",
        "seo_title": "Free QR Code Generator Online (PNG & SVG) - ToolNest",
        "meta_description": "Generate high-quality QR codes for URLs, UPI payments, emails, and Wi-Fi networks in PNG and SVG formats.",
        "canonical_path": "/qr-code-generator",
        "how_to_steps": ["Choose QR content type", "Enter data (URL, UPI ID, text, etc.)", "Customize colors and size", "Download PNG or SVG"],
    },
    # Text Utilities (Browser-Only)
    {
        "category_slug": "text",
        "slug": "word-counter",
        "name": "Word Counter",
        "tool_type": "browser",
        "endpoint": None,
        "description": "Count words, characters, sentences, paragraphs, and reading time in real time.",
        "seo_title": "Online Word and Character Counter - ToolNest",
        "meta_description": "Instant client-side word count, character count, and reading time calculation with zero lag.",
        "canonical_path": "/word-counter",
        "how_to_steps": ["Type or paste your text", "View instant live counts", "Inspect reading time and metrics"],
    },
    {
        "category_slug": "text",
        "slug": "case-converter",
        "name": "Case Converter",
        "tool_type": "browser",
        "endpoint": None,
        "description": "Convert text into UPPERCASE, lowercase, Title Case, camelCase, snake_case, and kebab-case.",
        "seo_title": "Online Case Converter Tool - ToolNest",
        "meta_description": "Transform text case between uppercase, lowercase, title case, camelCase, snake_case, and kebab-case in your browser.",
        "canonical_path": "/case-converter",
        "how_to_steps": ["Enter text into the box", "Click desired case transformation", "Click Copy to Clipboard"],
    },
    # Developer Tools (Browser-Only)
    {
        "category_slug": "developer",
        "slug": "json-formatter",
        "name": "JSON Formatter & Validator",
        "tool_type": "browser",
        "endpoint": None,
        "description": "Format, beautify, minify, and validate JSON data securely in your browser.",
        "seo_title": "Secure Online JSON Formatter & Validator - ToolNest",
        "meta_description": "Format and validate JSON completely in your browser. Zero text uploaded to servers for total privacy.",
        "canonical_path": "/json-formatter",
        "how_to_steps": ["Paste JSON text", "Choose indentation (2 or 4 spaces) or minify", "Inspect validation errors with line/col", "Copy formatted JSON"],
    },
    # Finance Calculators (Browser-Only)
    {
        "category_slug": "finance",
        "slug": "emi-calculator",
        "name": "EMI Calculator",
        "tool_type": "calculator",
        "endpoint": None,
        "description": "Calculate monthly loan EMI, total interest, and complete month-by-month repayment schedule.",
        "seo_title": "Loan EMI Calculator with Repayment Schedule - ToolNest",
        "meta_description": "Calculate exact home loan, car loan, or personal loan EMIs in INR with month-by-month schedule.",
        "canonical_path": "/emi-calculator",
        "how_to_steps": ["Enter loan principal amount", "Enter annual interest rate", "Enter tenure in years or months", "View EMI, total interest, and schedule"],
    },
    {
        "category_slug": "finance",
        "slug": "sip-calculator",
        "name": "SIP Calculator",
        "tool_type": "calculator",
        "endpoint": None,
        "description": "Calculate mutual fund SIP investment returns with optional yearly step-up.",
        "seo_title": "SIP Calculator with Step-Up Returns - ToolNest",
        "meta_description": "Calculate mutual fund SIP future value and compounding returns with annual step-up percentage in INR.",
        "canonical_path": "/sip-calculator",
        "how_to_steps": ["Enter monthly investment amount", "Enter expected annual return rate (%)", "Enter investment duration in years", "Optionally add step-up percentage", "View total wealth generated"],
    },
    {
        "category_slug": "finance",
        "slug": "gst-calculator",
        "name": "GST Calculator",
        "tool_type": "calculator",
        "endpoint": None,
        "description": "Calculate inclusive and exclusive GST with India GST 2.0 slabs (0%, 5%, 18%, 40%).",
        "seo_title": "India GST 2.0 Calculator (Add or Remove GST) - ToolNest",
        "meta_description": "Accurately add or remove Indian GST with current slabs (0%, 5%, 18%, 40%) and CGST/SGST/IGST breakdown.",
        "canonical_path": "/gst-calculator",
        "how_to_steps": ["Enter base or gross amount", "Select GST slab rate or custom percent", "Select Add GST or Remove GST", "Toggle inter-state (IGST) or intra-state (CGST/SGST)"],
    },
]

DEFAULT_SETTINGS = [
    {"key": "daily_server_uses", "value": 20, "description": "Free server-based tool uses per visitor per day"},
    {"key": "image_max_bytes", "value": 5242880, "description": "Max image size in bytes (5 MB)"},
    {"key": "pdf_max_bytes", "value": 10485760, "description": "Max PDF size in bytes (10 MB)"},
    {"key": "request_max_bytes", "value": 15728640, "description": "Max total request size in bytes (15 MB)"},
    {"key": "max_files_per_request", "value": 5, "description": "Max files per upload request"},
    {"key": "max_pdf_to_image_pages", "value": 15, "description": "Max pages for PDF to image conversion"},
    {"key": "max_processing_seconds", "value": 45, "description": "Processing timeout limit in seconds"},
    {"key": "gst_rates", "value": [0, 5, 18, 40], "description": "India GST 2.0 standard percentage slabs"},
    {"key": "ads_enabled", "value": False, "description": "Ad slots enabled switch (disabled until AdSense approval)"},
    {"key": "api_base_url", "value": "http://localhost:8000", "description": "Public URL of the backend API"},
]


def seed_database() -> None:
    """Seed categories, tools, and default site settings."""
    try:
        session_factory = get_session_factory()
    except DatabaseConfigurationError as e:
        print(f"Skipping seeding: {e}", file=sys.stderr)
        return
    except Exception as e:
        print(f"Database error during seeding: {e}", file=sys.stderr)
        return

    with session_factory() as session:
        # 1. Seed Categories
        category_map = {}
        for cat_data in CATEGORIES:
            cat = session.scalar(select(Category).where(Category.slug == cat_data["slug"]))
            if not cat:
                cat = Category(
                    slug=cat_data["slug"],
                    name=cat_data["name"],
                    description=cat_data["description"],
                    sort_order=cat_data["sort_order"],
                    is_active=True,
                )
                session.add(cat)
                session.flush()
                print(f"Created category: {cat.name}")
            category_map[cat.slug] = cat.id

        # 2. Seed Tools
        for tool_data in TOOLS:
            tool = session.scalar(select(Tool).where(Tool.slug == tool_data["slug"]))
            cat_id = category_map.get(tool_data["category_slug"])
            if not tool:
                tool = Tool(
                    slug=tool_data["slug"],
                    name=tool_data["name"],
                    category_id=cat_id,
                    tool_type=tool_data["tool_type"],
                    endpoint=tool_data["endpoint"],
                    description=tool_data["description"],
                    seo_title=tool_data["seo_title"],
                    meta_description=tool_data["meta_description"],
                    canonical_path=tool_data["canonical_path"],
                    how_to_steps=tool_data["how_to_steps"],
                    is_active=True,
                )
                session.add(tool)
                print(f"Created tool: {tool.name}")
            else:
                tool.category_id = cat_id
                tool.endpoint = tool_data["endpoint"]

        # 3. Seed Default Settings
        for setting_data in DEFAULT_SETTINGS:
            setting = session.scalar(select(SiteSetting).where(SiteSetting.key == setting_data["key"]))
            if not setting:
                setting = SiteSetting(
                    key=setting_data["key"],
                    value=setting_data["value"],
                    description=setting_data["description"],
                )
                session.add(setting)
                print(f"Created setting: {setting.key}")

        session.commit()
        print("Database seed completed successfully.")


if __name__ == "__main__":
    seed_database()
