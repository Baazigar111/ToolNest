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
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains; preload"


def test_openapi_docs_accessible(client: TestClient):
    """Verify /openapi.json loads successfully in development / testing mode."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/health" in schema["paths"]


def test_production_docs_disabled(monkeypatch, sqlite_engine):
    """Verify OpenAPI and Swagger /docs are disabled in production environment."""
    from app.config import get_settings
    from app.main import create_app

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ENABLE_API_DOCS", "false")
    get_settings.cache_clear()

    prod_app = create_app(engine=sqlite_engine)
    with TestClient(prod_app) as prod_client:
        assert prod_client.get("/docs").status_code == 404
        assert prod_client.get("/openapi.json").status_code == 404

