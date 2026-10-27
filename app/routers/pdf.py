"""PDF API router exposing endpoints for Merge, Split, Compress, PDF to Images, and Images to PDF."""

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ToolDisabledError
from app.services.file_validator import FileValidator
from app.services.pdf_service import PDFService
from app.services.tool_service import ToolService
from app.services.usage_service import UsageService

router = APIRouter(prefix="/api/pdf", tags=["PDF Processing"])


@router.post("/merge", summary="Merge Multiple PDFs")
async def merge_pdfs(
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_db),
) -> Response:
    """Merge between 2 and 5 PDF files into a single unified document."""
    tool = ToolService.get_tool_by_slug("merge-pdf", session)
    if tool and not tool.is_active:
        raise ToolDisabledError()

    FileValidator.validate_file_count(files, min_files=2)
    is_error = False
    total_bytes = 0
    pdf_buffers: list[bytes] = []

    try:
        for f in files:
            content = await FileValidator.read_and_validate_pdf(f)
            total_bytes += len(content)
            pdf_buffers.append(content)

        merged_bytes = PDFService.merge_pdfs(pdf_buffers)
        return Response(
            content=merged_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="merged.pdf"'},
        )
    except Exception:
        is_error = True
        raise
    finally:
        if tool:
            UsageService.record_usage(tool.id, is_error=is_error, bytes_count=total_bytes)


@router.post("/split", summary="Split PDF by Pages or Extract Ranges")
async def split_pdf(
    file: UploadFile = File(...),
    ranges: str | None = Form(None),
    session: Session = Depends(get_db),
) -> Response:
    """Split a PDF into a ZIP archive of individual pages or extract specific page ranges."""
    tool = ToolService.get_tool_by_slug("split-pdf", session)
    if tool and not tool.is_active:
        raise ToolDisabledError()

    is_error = False
    content_len = 0
    try:
        content = await FileValidator.read_and_validate_pdf(file)
        content_len = len(content)
        result_bytes, filename, media_type = PDFService.split_pdf(content, page_ranges=ranges)
        return Response(
            content=result_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception:
        is_error = True
        raise
    finally:
        if tool:
            UsageService.record_usage(tool.id, is_error=is_error, bytes_count=content_len)


@router.post("/compress", summary="Compress PDF File Size")
async def compress_pdf(
    file: UploadFile = File(...),
    level: str = Form("medium"),
    session: Session = Depends(get_db),
) -> Response:
    """Compress PDF document using stream deflation and object deduplication."""
    tool = ToolService.get_tool_by_slug("compress-pdf", session)
    if tool and not tool.is_active:
        raise ToolDisabledError()

    is_error = False
    content_len = 0
    try:
        content = await FileValidator.read_and_validate_pdf(file)
        content_len = len(content)
        compressed_bytes = PDFService.compress_pdf(content, compression_level=level)
        return Response(
            content=compressed_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="compressed.pdf"'},
        )
    except Exception:
        is_error = True
        raise
    finally:
        if tool:
            UsageService.record_usage(tool.id, is_error=is_error, bytes_count=content_len)


@router.post("/to-images", summary="Convert PDF Pages to Images")
@router.post("/to-image", summary="Convert PDF Pages to Images")
async def pdf_to_images(
    file: UploadFile = File(...),
    format: str = Form("png"),
    dpi: int = Form(150),
    session: Session = Depends(get_db),
) -> Response:
    """Convert PDF pages into high-resolution PNG or JPEG images (ZIP archive for multi-page)."""
    tool = ToolService.get_tool_by_slug("pdf-to-images", session) or ToolService.get_tool_by_slug("pdf-to-image", session)
    if tool and not tool.is_active:
        raise ToolDisabledError()

    is_error = False
    content_len = 0
    try:
        content = await FileValidator.read_and_validate_pdf(file)
        content_len = len(content)
        result_bytes, filename, media_type = PDFService.pdf_to_images(content, image_format=format, dpi=dpi)
        return Response(
            content=result_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception:
        is_error = True
        raise
    finally:
        if tool:
            UsageService.record_usage(tool.id, is_error=is_error, bytes_count=content_len)


@router.post("/from-images", summary="Convert Images to PDF")
@router.post("/to-pdf", summary="Convert Images to PDF")
async def images_to_pdf(
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_db),
) -> Response:
    """Convert up to 5 uploaded images into a single clean PDF document."""
    tool = ToolService.get_tool_by_slug("images-to-pdf", session)
    if tool and not tool.is_active:
        raise ToolDisabledError()

    FileValidator.validate_file_count(files, min_files=1)
    is_error = False
    total_bytes = 0
    image_buffers: list[bytes] = []

    try:
        for f in files:
            img_bytes, _ = await FileValidator.read_and_validate_image(f)
            total_bytes += len(img_bytes)
            image_buffers.append(img_bytes)

        pdf_bytes = PDFService.images_to_pdf(image_buffers)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="images_combined.pdf"'},
        )
    except Exception:
        is_error = True
        raise
    finally:
        if tool:
            UsageService.record_usage(tool.id, is_error=is_error, bytes_count=total_bytes)
