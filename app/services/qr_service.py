"""QR code generation service supporting customizable size, colors, error correction, and formats."""

import io

import qrcode
from qrcode.image.svg import SvgPathImage

from app.errors import ToolNestError

ERROR_CORRECTION_MAP = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}


class QRService:
    """Generates PNG and SVG QR codes safely in-memory."""

    @staticmethod
    def generate_qr(
        data: str,
        box_size: int = 10,
        border: int = 4,
        error_correction: str = "M",
        fill_color: str = "#000000",
        back_color: str = "#FFFFFF",
        output_format: str = "png",
    ) -> tuple[bytes, str]:
        """
        Generate QR code as raw bytes.
        Returns (bytes, media_type).
        """
        clean_data = data.strip()
        if not clean_data:
            raise ToolNestError(
                code="EMPTY_DATA",
                message="Text or URL is required to generate a QR code",
                status_code=400,
            )
        if len(clean_data) > 2048:
            raise ToolNestError(
                code="DATA_TOO_LONG",
                message="QR code data cannot exceed 2048 characters",
                status_code=400,
            )

        ec_level = ERROR_CORRECTION_MAP.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_M)
        fmt = output_format.lower()

        if fmt == "svg":
            qr = qrcode.QRCode(
                version=None,
                error_correction=ec_level,
                box_size=max(1, min(box_size, 50)),
                border=max(0, min(border, 20)),
                image_factory=SvgPathImage,
            )
            qr.add_data(clean_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color=fill_color, back_color=back_color)
            stream = io.BytesIO()
            img.save(stream)
            return stream.getvalue(), "image/svg+xml"

        # Default: PNG
        qr = qrcode.QRCode(
            version=None,
            error_correction=ec_level,
            box_size=max(1, min(box_size, 50)),
            border=max(0, min(border, 20)),
        )
        qr.add_data(clean_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        stream = io.BytesIO()
        img.save(stream, format="PNG")
        return stream.getvalue(), "image/png"
