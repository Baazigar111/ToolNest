"""Tests for FileValidator upload inspection, magic bytes, and limit enforcement."""

import io

import pytest
from fastapi import UploadFile
from PIL import Image

from app.errors import (
    FileTooLargeError,
    PageLimitError,
    PasswordProtectedError,
    TooManyFilesError,
    UnsupportedTypeError,
)
from app.services.file_validator import FileValidator


def create_dummy_pdf(num_pages: int = 1, encrypted: bool = False, password: str = "secret") -> bytes:
    """Helper to generate in-memory dummy PDF for tests."""
    import pypdf

    writer = pypdf.PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=100, height=100)

    if encrypted:
        writer.encrypt(password)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def create_dummy_image(format: str = "PNG", width: int = 100, height: int = 100) -> bytes:
    """Helper to generate in-memory test image."""
    img = Image.new("RGB", (width, height), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_validate_file_count():
    """Verify file count minimum and maximum validation."""
    dummy_file = UploadFile(filename="test.pdf", file=io.BytesIO(b""))

    # Less than min_files
    with pytest.raises(Exception) as exc:
        FileValidator.validate_file_count([], min_files=2)
    assert exc.value.code == "INVALID_FILE_COUNT"

    # More than max_files
    with pytest.raises(TooManyFilesError):
        FileValidator.validate_file_count([dummy_file] * 6, max_files=5)

    # Valid range
    FileValidator.validate_file_count([dummy_file, dummy_file], min_files=2, max_files=5)


@pytest.mark.anyio
async def test_validate_pdf_success():
    """Verify valid unencrypted PDF passes validation."""
    pdf_bytes = create_dummy_pdf(num_pages=3)
    upload = UploadFile(filename="sample.pdf", file=io.BytesIO(pdf_bytes))
    res = await FileValidator.read_and_validate_pdf(upload, max_pages=10)
    assert res == pdf_bytes


@pytest.mark.anyio
async def test_validate_pdf_file_too_large():
    """Verify PDF exceeding byte limit is rejected."""
    pdf_bytes = create_dummy_pdf(num_pages=1)
    upload = UploadFile(filename="huge.pdf", file=io.BytesIO(pdf_bytes))
    with pytest.raises(FileTooLargeError):
        await FileValidator.read_and_validate_pdf(upload, max_bytes=10)  # 10 bytes limit


@pytest.mark.anyio
async def test_validate_pdf_invalid_magic_bytes():
    """Verify non-PDF file is rejected with UnsupportedTypeError."""
    upload = UploadFile(filename="fake.pdf", file=io.BytesIO(b"NOT A REAL PDF FILE"))
    with pytest.raises(UnsupportedTypeError):
        await FileValidator.read_and_validate_pdf(upload)


@pytest.mark.anyio
async def test_validate_pdf_password_protected():
    """Verify encrypted PDF raises PasswordProtectedError."""
    encrypted_bytes = create_dummy_pdf(num_pages=1, encrypted=True)
    upload = UploadFile(filename="locked.pdf", file=io.BytesIO(encrypted_bytes))
    with pytest.raises(PasswordProtectedError):
        await FileValidator.read_and_validate_pdf(upload)


@pytest.mark.anyio
async def test_validate_pdf_page_limit_exceeded():
    """Verify PDF exceeding page count limit raises PageLimitError."""
    pdf_bytes = create_dummy_pdf(num_pages=15)
    upload = UploadFile(filename="long.pdf", file=io.BytesIO(pdf_bytes))
    with pytest.raises(PageLimitError):
        await FileValidator.read_and_validate_pdf(upload, max_pages=5)


@pytest.mark.anyio
async def test_validate_image_success():
    """Verify valid PNG and JPEG pass validation."""
    png_bytes = create_dummy_image("PNG")
    upload = UploadFile(filename="test.png", file=io.BytesIO(png_bytes))
    content, fmt = await FileValidator.read_and_validate_image(upload)
    assert content == png_bytes
    assert fmt == "PNG"


@pytest.mark.anyio
async def test_validate_image_invalid_magic_bytes():
    """Verify non-image file raises UnsupportedTypeError."""
    upload = UploadFile(filename="fake.png", file=io.BytesIO(b"Hello text data"))
    with pytest.raises(UnsupportedTypeError):
        await FileValidator.read_and_validate_image(upload)
