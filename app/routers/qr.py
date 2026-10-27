"""QR Code API router supporting text/URL to PNG and SVG generation."""

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ToolDisabledError
from app.services.qr_service import QRService
from app.services.tool_service import ToolService
from app.services.usage_service import UsageService

router = APIRouter(prefix="/api/qr", tags=["QR Code"])


class QRCodeRequest(BaseModel):
    data: str = Field(..., description="Text or URL to encode", max_length=2048)
    box_size: int = Field(default=10, ge=1, le=50, description="Size of each box/pixel")
    border: int = Field(default=4, ge=0, le=20, description="Border width in boxes")
    error_correction: str = Field(default="M", pattern="^(?i)[LMQH]$", description="Error correction level (L, M, Q, H)")
    fill_color: str = Field(default="#000000", description="Foreground color")
    back_color: str = Field(default="#FFFFFF", description="Background color")
    format: str = Field(default="png", pattern="^(?i)(png|svg)$", description="Output format (png or svg)")


@router.post("", summary="Generate QR Code Image")
@router.post("/generate", summary="Generate QR Code Image")
def generate_qr_code(
    payload: QRCodeRequest,
    session: Session = Depends(get_db),
) -> Response:
    """Generate customizable QR code image in PNG or SVG format."""
    tool = ToolService.get_tool_by_slug("qr-code-generator", session)
    if tool and not tool.is_active:
        raise ToolDisabledError()

    is_error = False
    qr_bytes = b""
    try:
        qr_bytes, media_type = QRService.generate_qr(
            data=payload.data,
            box_size=payload.box_size,
            border=payload.border,
            error_correction=payload.error_correction,
            fill_color=payload.fill_color,
            back_color=payload.back_color,
            output_format=payload.format,
        )
    except Exception:
        is_error = True
        raise
    finally:
        if tool:
            UsageService.record_usage(
                tool_id=tool.id,
                is_error=is_error,
                bytes_count=len(qr_bytes),
            )

    ext = payload.format.lower()
    return Response(
        content=qr_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="qrcode.{ext}"'},
    )
