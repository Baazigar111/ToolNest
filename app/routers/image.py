"""Image API router exposing endpoints for Compress, Resize, Convert, and Crop operations."""

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ToolDisabledError, ToolNestError
from app.services.file_validator import FileValidator
from app.services.image_service import ImageService
from app.services.pdf_service import PDFService
from app.services.tool_service import ToolService
from app.services.usage_service import UsageService

router = APIRouter(prefix="/api/image", tags=["Image Processing"])


@router.post("/compress", summary="Compress Image")
async def compress_image(
    file: UploadFile = File(...),
    quality: int = Form(80),
    session: Session = Depends(get_db),
) -> Response:
    """Compress image with configurable quality factor and stream optimization."""
    tool = ToolService.get_tool_by_slug("compress-image", session)
    if tool and not tool.is_active:
        raise ToolDisabledError()

    is_error = False
    content_len = 0
    try:
        content, _ = await FileValidator.read_and_validate_image(file)
        content_len = len(content)
        result_bytes, filename, media_type = ImageService.compress_image(content, quality=quality)
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


@router.post("/resize", summary="Resize Image Dimensions")
async def resize_image(
    file: UploadFile = File(...),
    width: int | None = Form(None),
    height: int | None = Form(None),
    percent: int | None = Form(None),
    maintain_aspect_ratio: bool = Form(True),
    session: Session = Depends(get_db),
) -> Response:
    """Resize image to specific pixel dimensions or scale percentage."""
    tool = ToolService.get_tool_by_slug("resize-image", session)
    if tool and not tool.is_active:
        raise ToolDisabledError()

    is_error = False
    content_len = 0
    try:
        content, _ = await FileValidator.read_and_validate_image(file)
        content_len = len(content)
        result_bytes, filename, media_type = ImageService.resize_image(
            content,
            width=width,
            height=height,
            percent=percent,
            maintain_aspect_ratio=maintain_aspect_ratio,
        )
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


@router.post("/convert", summary="Convert Image Format")
async def convert_image(
    file: UploadFile = File(...),
    target_format: str = Form(...),
    session: Session = Depends(get_db),
) -> Response:
    """Convert image format between JPG, PNG, and WebP."""
    tool = ToolService.get_tool_by_slug("convert-image", session)
    if tool and not tool.is_active:
        raise ToolDisabledError()

    is_error = False
    content_len = 0
    try:
        content, _ = await FileValidator.read_and_validate_image(file)
        content_len = len(content)
        result_bytes, filename, media_type = ImageService.convert_image(
            content,
            target_format=target_format,
        )
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


@router.post("/crop", summary="Crop Rectangular Image Region")
async def crop_image(
    file: UploadFile = File(...),
    x: int = Form(...),
    y: int = Form(...),
    width: int = Form(...),
    height: int = Form(...),
    session: Session = Depends(get_db),
) -> Response:
    """Crop image to specific coordinates and dimensions."""
    tool = ToolService.get_tool_by_slug("crop-image", session)
    if tool and not tool.is_active:
        raise ToolDisabledError()

    is_error = False
    content_len = 0
    try:
        content, _ = await FileValidator.read_and_validate_image(file)
        content_len = len(content)
        result_bytes, filename, media_type = ImageService.crop_image(
            content,
            x=x,
            y=y,
            width=width,
            height=height,
        )
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


@router.post("/to-pdf", summary="Convert Images to PDF")
@router.post("/from-images", summary="Convert Images to PDF")
async def images_to_pdf(
    files: list[UploadFile] = File(default=[]),
    file: UploadFile | None = File(default=None),
    session: Session = Depends(get_db),
) -> Response:
    """Convert up to 5 uploaded images into a single clean PDF document."""
    tool = ToolService.get_tool_by_slug("image-to-pdf", session) or ToolService.get_tool_by_slug("images-to-pdf", session)
    if tool and not tool.is_active:
        raise ToolDisabledError()

    upload_list = [f for f in files if f.filename]
    if file and file.filename:
        upload_list.append(file)
    if not upload_list:
        raise ToolNestError("Please select at least one image file.")

    FileValidator.validate_file_count(upload_list, min_files=1)
    is_error = False
    total_bytes = 0
    image_buffers: list[bytes] = []

    try:
        for f in upload_list:
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

