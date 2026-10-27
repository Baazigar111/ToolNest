"""File validation service ensuring file types, magic bytes, limits, and integrity before processing."""

import io

import pypdf
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.config import get_settings
from app.errors import (
    CorruptFileError,
    FileTooLargeError,
    PageLimitError,
    PasswordProtectedError,
    ToolNestError,
    TooManyFilesError,
    UnsupportedTypeError,
)

PDF_MAGIC = b"%PDF-"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
RIFF_MAGIC = b"RIFF"
WEBP_MAGIC = b"WEBP"


class FileValidator:
    """Validates uploaded files for magic signatures, size, page counts, and corruption."""

    @classmethod
    def validate_file_count(
        cls,
        files: list[UploadFile],
        min_files: int = 1,
        max_files: int | None = None,
    ) -> None:
        """Validate the number of uploaded files."""
        settings = get_settings()
        limit = max_files or settings.max_files_per_request
        if len(files) < min_files:
            raise ToolNestError(
                code="INVALID_FILE_COUNT",
                message=f"At least {min_files} file{'s' if min_files > 1 else ''} required for this operation",
                status_code=400,
            )
        if len(files) > limit:
            raise TooManyFilesError(f"You can upload up to {limit} files at a time")

    @classmethod
    async def read_and_validate_pdf(
        cls,
        file: UploadFile,
        max_bytes: int | None = None,
        max_pages: int | None = None,
    ) -> bytes:
        """
        Read PDF UploadFile, check size, magic bytes, password encryption, and page limit.
        Returns raw file bytes in memory.
        """
        settings = get_settings()
        limit_bytes = max_bytes or settings.pdf_max_bytes
        limit_pages = max_pages or settings.max_pdf_merge_split_pages

        content = await file.read()
        if len(content) > limit_bytes:
            raise FileTooLargeError(
                f"PDF exceeds the maximum allowable size of {limit_bytes // (1024 * 1024)} MB"
            )

        if not content.startswith(PDF_MAGIC):
            raise UnsupportedTypeError("Uploaded file is not a valid PDF document")

        # Check for PDF corruption, encryption, and page counts
        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                raise PasswordProtectedError("This PDF is password protected. Remove the password and try again")

            num_pages = len(reader.pages)
            if num_pages == 0:
                raise CorruptFileError("The uploaded PDF contains no pages")
            if num_pages > limit_pages:
                raise PageLimitError(
                    f"This PDF has {num_pages} pages, which exceeds the supported limit of {limit_pages} pages"
                )
        except (PasswordProtectedError, PageLimitError):
            raise
        except Exception as e:
            raise CorruptFileError(f"Could not read PDF: {e}") from e

        return content

    @classmethod
    async def read_and_validate_image(
        cls,
        file: UploadFile,
        max_bytes: int | None = None,
        allowed_formats: tuple[str, ...] = ("JPEG", "PNG", "WEBP"),
    ) -> tuple[bytes, str]:
        """
        Read image UploadFile, check size, verify format with Pillow, and validate dimension limits.
        Returns tuple of (raw bytes, format string).
        """
        settings = get_settings()
        limit_bytes = max_bytes or settings.image_max_bytes

        content = await file.read()
        if len(content) > limit_bytes:
            raise FileTooLargeError(
                f"Image exceeds the maximum allowable size of {limit_bytes // (1024 * 1024)} MB"
            )

        # Magic bytes preliminary check
        is_png = content.startswith(PNG_MAGIC)
        is_jpeg = content.startswith(JPEG_MAGIC)
        is_webp = content.startswith(RIFF_MAGIC) and WEBP_MAGIC in content[:16]

        if not (is_png or is_jpeg or is_webp):
            raise UnsupportedTypeError("Please upload a valid JPEG, PNG, or WebP image")

        try:
            with Image.open(io.BytesIO(content)) as img:
                img_format = (img.format or "").upper()
                if img_format not in allowed_formats:
                    raise UnsupportedTypeError(
                        f"Image format '{img_format}' is not supported. Use {', '.join(allowed_formats)}"
                    )

                width, height = img.size
                if width > settings.max_image_side_px or height > settings.max_image_side_px:
                    raise ToolNestError(
                        code="IMAGE_TOO_LARGE",
                        message=f"Image dimensions ({width}x{height}) exceed maximum allowed side of {settings.max_image_side_px}px",
                        status_code=400,
                    )
                if (width * height) > settings.max_image_pixels:
                    raise ToolNestError(
                        code="IMAGE_TOO_LARGE",
                        message="Image pixel count exceeds maximum supported resolution of 25 megapixels",
                        status_code=400,
                    )
                return content, img_format
        except (UnsupportedTypeError, ToolNestError):
            raise
        except UnidentifiedImageError as err:
            raise CorruptFileError("Could not decode image data. Check that the image opens on your device") from err
        except Exception as err:
            raise CorruptFileError(f"Image validation failed: {err}") from err
