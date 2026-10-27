"""Image Processing Service using Pillow for Compression, Resizing, Conversion, and Cropping."""

import io

from PIL import Image

from app.errors import CorruptFileError, ToolNestError


class ImageService:
    """High-performance in-memory image transformations with strict resource management."""

    @staticmethod
    def compress_image(
        image_bytes: bytes,
        quality: int = 80,
    ) -> tuple[bytes, str, str]:
        """
        Compress an image while preserving its format.
        Returns (compressed_bytes, filename, media_type).
        """
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                fmt = (img.format or "JPEG").upper()
                out_stream = io.BytesIO()

                if fmt in ("JPEG", "JPG"):
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img.save(
                        out_stream,
                        format="JPEG",
                        quality=max(1, min(quality, 100)),
                        optimize=True,
                        progressive=True,
                    )
                    ext = "jpg"
                    media_type = "image/jpeg"
                elif fmt == "PNG":
                    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                        img.save(out_stream, format="PNG", optimize=True, compress_level=9)
                    else:
                        img.save(out_stream, format="PNG", optimize=True, compress_level=9)
                    ext = "png"
                    media_type = "image/png"
                elif fmt == "WEBP":
                    img.save(
                        out_stream,
                        format="WEBP",
                        quality=max(1, min(quality, 100)),
                        method=6,
                    )
                    ext = "webp"
                    media_type = "image/webp"
                else:
                    # Fallback to JPEG
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img.save(out_stream, format="JPEG", quality=quality, optimize=True)
                    ext = "jpg"
                    media_type = "image/jpeg"

                result_bytes = out_stream.getvalue()
                return result_bytes, f"compressed.{ext}", media_type
        except Exception as e:
            raise CorruptFileError(f"Image compression failed: {e}") from e

    @staticmethod
    def resize_image(
        image_bytes: bytes,
        width: int | None = None,
        height: int | None = None,
        percent: int | None = None,
        maintain_aspect_ratio: bool = True,
    ) -> tuple[bytes, str, str]:
        """
        Resize image by dimensions or percentage scale factor.
        Returns (resized_bytes, filename, media_type).
        """
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                orig_w, orig_h = img.size
                target_w = orig_w
                target_h = orig_h

                if percent is not None and percent > 0:
                    scale = percent / 100.0
                    target_w = max(1, int(orig_w * scale))
                    target_h = max(1, int(orig_h * scale))
                elif width is not None and height is not None:
                    if maintain_aspect_ratio:
                        aspect = orig_w / orig_h
                        if width / height > aspect:
                            target_w = max(1, int(height * aspect))
                            target_h = height
                        else:
                            target_w = width
                            target_h = max(1, int(width / aspect))
                    else:
                        target_w = width
                        target_h = height
                elif width is not None:
                    target_w = width
                    target_h = max(1, int(orig_h * (width / orig_w)))
                elif height is not None:
                    target_h = height
                    target_w = max(1, int(orig_w * (height / orig_h)))
                else:
                    raise ToolNestError(
                        code="INVALID_DIMENSIONS",
                        message="Please specify target width, height, or resize percentage",
                        status_code=400,
                    )

                resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                fmt = (img.format or "JPEG").upper()
                ext = "jpg" if fmt in ("JPEG", "JPG") else fmt.lower()
                media_type = "image/jpeg" if ext == "jpg" else f"image/{ext}"

                out_stream = io.BytesIO()
                save_kwargs = {}
                if fmt in ("JPEG", "JPG"):
                    if resized.mode != "RGB":
                        resized = resized.convert("RGB")
                    save_kwargs["quality"] = 90
                resized.save(out_stream, format=fmt, **save_kwargs)

                return out_stream.getvalue(), f"resized_{target_w}x{target_h}.{ext}", media_type
        except ToolNestError:
            raise
        except Exception as e:
            raise CorruptFileError(f"Image resizing failed: {e}") from e

    @staticmethod
    def convert_image(
        image_bytes: bytes,
        target_format: str,
    ) -> tuple[bytes, str, str]:
        """
        Convert image between JPEG, PNG, and WebP.
        Returns (converted_bytes, filename, media_type).
        """
        fmt = target_format.upper().strip()
        if fmt in ("JPG", "JPEG"):
            out_fmt = "JPEG"
            ext = "jpg"
            media_type = "image/jpeg"
        elif fmt == "PNG":
            out_fmt = "PNG"
            ext = "png"
            media_type = "image/png"
        elif fmt == "WEBP":
            out_fmt = "WEBP"
            ext = "webp"
            media_type = "image/webp"
        else:
            raise ToolNestError(
                code="UNSUPPORTED_FORMAT",
                message=f"Target format '{target_format}' is not supported. Use JPG, PNG, or WebP",
                status_code=400,
            )

        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                out_stream = io.BytesIO()

                if out_fmt == "JPEG":
                    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                        # Fill transparent parts with clean white background
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        img_rgba = img.convert("RGBA")
                        background.paste(img_rgba, mask=img_rgba.split()[3])
                        img_to_save = background
                    elif img.mode != "RGB":
                        img_to_save = img.convert("RGB")
                    else:
                        img_to_save = img
                    img_to_save.save(out_stream, format="JPEG", quality=90, optimize=True)
                elif out_fmt == "PNG":
                    img.save(out_stream, format="PNG", optimize=True)
                elif out_fmt == "WEBP":
                    img.save(out_stream, format="WEBP", quality=90)

                return out_stream.getvalue(), f"converted.{ext}", media_type
        except ToolNestError:
            raise
        except Exception as e:
            raise CorruptFileError(f"Image conversion failed: {e}") from e

    @staticmethod
    def crop_image(
        image_bytes: bytes,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> tuple[bytes, str, str]:
        """
        Crop rectangular region from image.
        Returns (cropped_bytes, filename, media_type).
        """
        if width <= 0 or height <= 0:
            raise ToolNestError(
                code="INVALID_CROP_BOUNDS",
                message="Crop width and height must be positive numbers",
                status_code=400,
            )

        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                orig_w, orig_h = img.size

                if x < 0 or y < 0 or (x + width) > orig_w or (y + height) > orig_h:
                    raise ToolNestError(
                        code="CROP_OUT_OF_BOUNDS",
                        message=f"Crop area ({x}, {y}, {width}, {height}) extends beyond image bounds ({orig_w}x{orig_h})",
                        status_code=400,
                    )

                cropped = img.crop((x, y, x + width, y + height))
                fmt = (img.format or "JPEG").upper()
                ext = "jpg" if fmt in ("JPEG", "JPG") else fmt.lower()
                media_type = "image/jpeg" if ext == "jpg" else f"image/{ext}"

                out_stream = io.BytesIO()
                save_kwargs = {}
                if fmt in ("JPEG", "JPG"):
                    if cropped.mode != "RGB":
                        cropped = cropped.convert("RGB")
                    save_kwargs["quality"] = 92
                cropped.save(out_stream, format=fmt, **save_kwargs)

                return out_stream.getvalue(), f"cropped.{ext}", media_type
        except ToolNestError:
            raise
        except Exception as e:
            raise CorruptFileError(f"Image cropping failed: {e}") from e
