"""Tests for QR Code generation service and API endpoint."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.tool import Tool
from app.services.qr_service import QRService


def test_qr_service_generate_png():
    """Verify PNG QR code generation."""
    qr_bytes, media_type = QRService.generate_qr("https://toolnest.example", output_format="png")
    assert media_type == "image/png"
    assert qr_bytes.startswith(b"\x89PNG")


def test_qr_service_generate_svg():
    """Verify SVG QR code generation."""
    qr_bytes, media_type = QRService.generate_qr("https://toolnest.example", output_format="svg")
    assert media_type == "image/svg+xml"
    assert b"<svg" in qr_bytes


def test_qr_service_empty_data_rejected():
    """Verify empty string raises ToolNestError."""
    with pytest.raises(Exception) as exc:
        QRService.generate_qr("   ")
    assert exc.value.code == "EMPTY_DATA"


def test_qr_api_endpoint(client: TestClient, db_session: Session):
    """Verify /api/qr/generate endpoint returns valid QR code and registers usage."""
    cat = Category(name="QR Tools", slug="qr", sort_order=1)
    db_session.add(cat)
    db_session.flush()

    tool = Tool(
        name="QR Code Generator",
        slug="qr-code-generator",
        category_id=cat.id,
        tool_type="qr",
        endpoint="/api/qr/generate",
        is_active=True,
    )
    db_session.add(tool)
    db_session.commit()

    res = client.post(
        "/api/qr/generate",
        json={
            "data": "https://example.com",
            "box_size": 10,
            "border": 4,
            "error_correction": "H",
            "format": "png",
        },
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert res.content.startswith(b"\x89PNG")


def test_qr_api_tool_disabled(client: TestClient, db_session: Session):
    """Verify disabled QR tool returns 503 Service Unavailable."""
    cat = Category(name="QR Tools", slug="qr", sort_order=1)
    db_session.add(cat)
    db_session.flush()

    tool = Tool(
        name="QR Code Generator",
        slug="qr-code-generator",
        category_id=cat.id,
        tool_type="qr",
        endpoint="/api/qr/generate",
        is_active=False,  # Disabled kill switch
    )
    db_session.add(tool)
    db_session.commit()

    res = client.post(
        "/api/qr/generate",
        json={"data": "https://example.com"},
    )
    assert res.status_code == 503
    data = res.json()
    assert data["code"] == "TOOL_DISABLED"
