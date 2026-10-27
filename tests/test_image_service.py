"""Tests for ImageService and /api/image routers."""

import io

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.tool import Tool
from app.services.image_service import ImageService


def create_test_image(format: str = "PNG", width: int = 100, height: int = 80) -> bytes:
    img = Image.new("RGB", (width, height), color=(255, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_compress_image():
    """Verify ImageService compresses image."""
    img_bytes = create_test_image("JPEG", 200, 200)
    compressed, filename, media_type = ImageService.compress_image(img_bytes, quality=50)
    assert media_type == "image/jpeg"
    assert len(compressed) > 0


def test_resize_image():
    """Verify ImageService resizes image dimensions accurately."""
    img_bytes = create_test_image("PNG", 200, 100)
    resized, filename, media_type = ImageService.resize_image(
        img_bytes,
        width=100,
        height=50,
        maintain_aspect_ratio=False,
    )
    with Image.open(io.BytesIO(resized)) as img:
        assert img.size == (100, 50)


def test_convert_image():
    """Verify ImageService converts format between PNG and WebP."""
    img_bytes = create_test_image("PNG", 100, 100)
    converted, filename, media_type = ImageService.convert_image(img_bytes, target_format="webp")
    assert media_type == "image/webp"
    with Image.open(io.BytesIO(converted)) as img:
        assert img.format == "WEBP"


def test_crop_image():
    """Verify ImageService crops specific subregion."""
    img_bytes = create_test_image("PNG", 200, 200)
    cropped, filename, media_type = ImageService.crop_image(img_bytes, x=10, y=10, width=50, height=60)
    with Image.open(io.BytesIO(cropped)) as img:
        assert img.size == (50, 60)


def test_image_api_compress_endpoint(client: TestClient, db_session: Session):
    """Verify /api/image/compress endpoint."""
    cat = Category(name="Image Tools", slug="image", sort_order=1)
    db_session.add(cat)
    db_session.flush()

    tool = Tool(name="Compress Image", slug="compress-image", category_id=cat.id, tool_type="image", is_active=True)
    db_session.add(tool)
    db_session.commit()

    raw_img = create_test_image("JPEG", 150, 150)
    res = client.post(
        "/api/image/compress",
        files={"file": ("photo.jpg", io.BytesIO(raw_img), "image/jpeg")},
        data={"quality": 75},
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"
