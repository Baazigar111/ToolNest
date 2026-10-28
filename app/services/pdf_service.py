"""PDF Processing Service supporting Merge, Split, Compress, PDF to Images, and Images to PDF."""

import io
import zipfile

import pikepdf
import pypdf
from PIL import Image

from app.config import get_settings
from app.errors import CorruptFileError, PageLimitError, ToolNestError


class PDFService:
    """High-performance in-memory PDF processing using PyMuPDF, pikepdf, and pypdf."""

    @staticmethod
    def merge_pdfs(pdf_contents: list[bytes]) -> bytes:
        """
        Merge multiple PDF byte streams into a single PDF document.
        Enforces max total page limits.
        """
        settings = get_settings()
        writer = pypdf.PdfWriter()
        total_pages = 0

        for content in pdf_contents:
            try:
                reader = pypdf.PdfReader(io.BytesIO(content))
                for page in reader.pages:
                    total_pages += 1
                    if total_pages > settings.max_pdf_merge_split_pages:
                        raise PageLimitError(
                            f"Total combined page count exceeds the maximum allowed limit of {settings.max_pdf_merge_split_pages} pages"
                        )
                    writer.add_page(page)
            except PageLimitError:
                raise
            except Exception as e:
                raise CorruptFileError(f"Failed to read PDF for merging: {e}") from e

        output_stream = io.BytesIO()
        writer.write(output_stream)
        return output_stream.getvalue()

    @staticmethod
    def split_pdf(pdf_content: bytes, page_ranges: str | None = None) -> tuple[bytes, str, str]:
        """
        Split a PDF by specific page ranges (e.g. '1-3,5') or split into individual pages in a ZIP archive.
        Returns (content_bytes, filename, media_type).
        """
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_content))
            total_pages = len(reader.pages)
        except Exception as e:
            raise CorruptFileError(f"Could not read PDF: {e}") from e

        if total_pages == 0:
            raise CorruptFileError("PDF has no pages to split")

        clean_ranges = (page_ranges or "").strip()

        # If specific range given (e.g. "1-3, 5")
        if clean_ranges:
            selected_pages: list[int] = []
            for part in clean_ranges.split(","):
                part = part.strip()
                if not part:
                    continue
                if "-" in part:
                    start_str, end_str = part.split("-", 1)
                    try:
                        start_page = int(start_str.strip())
                        end_page = int(end_str.strip())
                    except ValueError:
                        raise ToolNestError(
                            code="INVALID_PAGE_RANGE",
                            message=f"Invalid page range format: '{part}'. Example format: '1-3, 5'",
                            status_code=400,
                        ) from None
                    if start_page < 1 or end_page > total_pages or start_page > end_page:
                        raise ToolNestError(
                            code="PAGE_OUT_OF_BOUNDS",
                            message=f"Page range '{part}' is out of bounds for a {total_pages}-page document",
                            status_code=400,
                        )
                    selected_pages.extend(range(start_page - 1, end_page))
                else:
                    try:
                        single_page = int(part)
                    except ValueError:
                        raise ToolNestError(
                            code="INVALID_PAGE_RANGE",
                            message=f"Invalid page number: '{part}'",
                            status_code=400,
                        ) from None
                    if single_page < 1 or single_page > total_pages:
                        raise ToolNestError(
                            code="PAGE_OUT_OF_BOUNDS",
                            message=f"Page {single_page} is out of bounds for a {total_pages}-page document",
                            status_code=400,
                        )
                    selected_pages.append(single_page - 1)

            if not selected_pages:
                raise ToolNestError(
                    code="EMPTY_SELECTION",
                    message="No valid pages specified for extraction",
                    status_code=400,
                )

            # Deduplicate while preserving order
            unique_pages = list(dict.fromkeys(selected_pages))

            writer = pypdf.PdfWriter()
            for p_idx in unique_pages:
                writer.add_page(reader.pages[p_idx])

            out_stream = io.BytesIO()
            writer.write(out_stream)
            return out_stream.getvalue(), "extracted_pages.pdf", "application/pdf"

        # Split all pages into a ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, page in enumerate(reader.pages, start=1):
                writer = pypdf.PdfWriter()
                writer.add_page(page)
                page_stream = io.BytesIO()
                writer.write(page_stream)
                zip_file.writestr(f"page_{idx}.pdf", page_stream.getvalue())

        return zip_buffer.getvalue(), "split_pages.zip", "application/zip"

    @staticmethod
    def compress_pdf(pdf_content: bytes, compression_level: str = "medium") -> bytes:
        """
        Compress PDF using pikepdf stream deflation, object deduplication, and PyMuPDF optimizations.
        """
        try:
            # First pass: pikepdf lossy-free stream deflation and structure clean
            with pikepdf.open(io.BytesIO(pdf_content)) as pdf:
                # Remove unreferenced objects & deduplicate streams
                pdf.remove_unreferenced_resources()
                out_stream = io.BytesIO()
                pdf.save(
                    out_stream,
                    compress_streams=True,
                    object_stream_mode=pikepdf.ObjectStreamMode.generate,
                    stream_decode_level=pikepdf.StreamDecodeLevel.generalized,
                )
                intermediate_bytes = out_stream.getvalue()
        except Exception:
            intermediate_bytes = pdf_content

        # Second pass: PyMuPDF garbage collection and compression
        try:
            import pymupdf as fitz
            doc = fitz.open(stream=intermediate_bytes, filetype="pdf")
            final_stream = io.BytesIO()
            doc.save(
                final_stream,
                garbage=4,
                deflate=True,
                clean=True,
            )
            doc.close()
            final_bytes = final_stream.getvalue()
            # If compressed size ended up larger, return the original content
            if len(final_bytes) < len(pdf_content):
                return final_bytes
            return pdf_content
        except Exception:
            return intermediate_bytes if len(intermediate_bytes) < len(pdf_content) else pdf_content

    @staticmethod
    def pdf_to_images(
        pdf_content: bytes,
        image_format: str = "png",
        dpi: int = 150,
    ) -> tuple[bytes, str, str]:
        """
        Render each page of a PDF document into an image.
        Returns (content_bytes, filename, media_type).
        If 1 page, returns raw image bytes. If multiple pages, returns a ZIP archive.
        """
        settings = get_settings()
        fmt = image_format.lower()
        if fmt not in ("png", "jpeg", "jpg"):
            fmt = "png"
        img_ext = "jpg" if fmt in ("jpeg", "jpg") else "png"
        media_type = "image/jpeg" if img_ext == "jpg" else "image/png"

        try:
            import pymupdf as fitz
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            total_pages = len(doc)
            if total_pages == 0:
                raise CorruptFileError("PDF has no pages to convert")
            if total_pages > settings.max_pdf_to_image_pages:
                raise PageLimitError(
                    f"PDF has {total_pages} pages, which exceeds the PDF to Images limit of {settings.max_pdf_to_image_pages} pages"
                )

            # Single page: return single image directly
            if total_pages == 1:
                page = doc[0]
                pix = page.get_pixmap(dpi=dpi)
                img_bytes = pix.tobytes(output=img_ext)
                doc.close()
                return img_bytes, f"page_1.{img_ext}", media_type

            # Multiple pages: return ZIP archive
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for idx, page in enumerate(doc, start=1):
                    pix = page.get_pixmap(dpi=dpi)
                    img_bytes = pix.tobytes(output=img_ext)
                    zip_file.writestr(f"page_{idx}.{img_ext}", img_bytes)
            doc.close()
            return zip_buffer.getvalue(), "pdf_images.zip", "application/zip"
        except (PageLimitError, CorruptFileError):
            raise
        except Exception as e:
            raise CorruptFileError(f"Failed to convert PDF to images: {e}") from e

    @staticmethod
    def images_to_pdf(image_contents: list[bytes]) -> bytes:
        """
        Convert up to 20 images into a single unified PDF document using Pillow.
        Handles RGBA transparency by composite on white background.
        """
        if not image_contents:
            raise ToolNestError(
                code="NO_IMAGES",
                message="At least one image is required to generate a PDF",
                status_code=400,
            )

        pil_images: list[Image.Image] = []
        try:
            for content in image_contents:
                img = Image.open(io.BytesIO(content))
                # Convert RGBA/LA or Palette with transparency to RGB on white background
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    img_rgba = img.convert("RGBA")
                    background.paste(img_rgba, mask=img_rgba.split()[3])
                    pil_images.append(background)
                elif img.mode != "RGB":
                    pil_images.append(img.convert("RGB"))
                else:
                    pil_images.append(img)

            first_img = pil_images[0]
            remaining = pil_images[1:] if len(pil_images) > 1 else []

            out_stream = io.BytesIO()
            first_img.save(
                out_stream,
                format="PDF",
                save_all=True,
                append_images=remaining,
                resolution=100.0,
            )
            return out_stream.getvalue()
        except Exception as e:
            raise CorruptFileError(f"Failed to convert images to PDF: {e}") from e
        finally:
            for img in pil_images:
                try:
                    img.close()
                except Exception:
                    pass
