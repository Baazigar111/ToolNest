"""Tests for PDFService and /api/pdf routers."""

import io

import pypdf
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.tool import Tool
from app.services.pdf_service import PDFService


def create_pdf(pages: int = 1) -> bytes:
    writer = pypdf.PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=100, height=100)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def create_image(format: str = "PNG") -> bytes:
    img = Image.new("RGB", (80, 80), color=(0, 128, 255))
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_merge_pdfs():
    """Verify PDFService merges multiple PDFs and preserves total page count."""
    pdf1 = create_pdf(2)
    pdf2 = create_pdf(3)
    merged = PDFService.merge_pdfs([pdf1, pdf2])

    reader = pypdf.PdfReader(io.BytesIO(merged))
    assert len(reader.pages) == 5


def test_split_pdf_ranges():
    """Verify PDFService extracts specific page ranges."""
    pdf = create_pdf(5)
    extracted, filename, media_type = PDFService.split_pdf(pdf, page_ranges="1-2, 5")
    assert media_type == "application/pdf"

    reader = pypdf.PdfReader(io.BytesIO(extracted))
    assert len(reader.pages) == 3


def test_split_pdf_all_to_zip():
    """Verify PDFService splits all pages into a ZIP file."""
    import zipfile

    pdf = create_pdf(3)
    zip_bytes, filename, media_type = PDFService.split_pdf(pdf, page_ranges=None)
    assert media_type == "application/zip"
    assert filename.endswith(".zip")

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        names = z.namelist()
        assert len(names) == 3
        assert "page_1.pdf" in names
        assert "page_2.pdf" in names
        assert "page_3.pdf" in names


def test_compress_pdf():
    """Verify PDFService runs compression without corruption."""
    pdf = create_pdf(2)
    compressed = PDFService.compress_pdf(pdf)
    assert len(compressed) > 0
    # Output must still be a valid PDF
    reader = pypdf.PdfReader(io.BytesIO(compressed))
    assert len(reader.pages) == 2


def test_pdf_to_images():
    """Verify PDFService converts pages into images."""
    pdf = create_pdf(1)
    img_bytes, filename, media_type = PDFService.pdf_to_images(pdf, image_format="png")
    assert media_type == "image/png"
    assert img_bytes.startswith(b"\x89PNG")


def test_images_to_pdf():
    """Verify PDFService packages multiple images into a valid PDF."""
    img1 = create_image("PNG")
    img2 = create_image("JPEG")
    pdf_bytes = PDFService.images_to_pdf([img1, img2])

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 2


def test_pdf_api_merge_endpoint(client: TestClient, db_session: Session):
    """Verify /api/pdf/merge endpoint."""
    cat = Category(name="PDF Tools", slug="pdf", sort_order=1)
    db_session.add(cat)
    db_session.flush()

    tool = Tool(name="Merge PDF", slug="merge-pdf", category_id=cat.id, tool_type="pdf", is_active=True)
    db_session.add(tool)
    db_session.commit()

    p1 = create_pdf(1)
    p2 = create_pdf(2)

    res = client.post(
        "/api/pdf/merge",
        files=[
            ("files", ("p1.pdf", io.BytesIO(p1), "application/pdf")),
            ("files", ("p2.pdf", io.BytesIO(p2), "application/pdf")),
        ],
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    reader = pypdf.PdfReader(io.BytesIO(res.content))
    assert len(reader.pages) == 3
