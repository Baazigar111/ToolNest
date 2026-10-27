"""Tests for GET /health endpoint and security headers."""

from fastapi.testclient import TestClient


def test_health_endpoint_success(client: TestClient):
    """Verify /health returns 200 OK and expected JSON structure."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_security_headers(client: TestClient):
    """Verify standard security headers are present on /health response."""
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_openapi_docs_accessible(client: TestClient):
    """Verify /openapi.json loads successfully without database dependency."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/health" in schema["paths"]
