"""Tests for ToolNest error contracts and exception handlers."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import (
    DailyLimitError,
    FileTooLargeError,
    PasswordProtectedError,
    RateLimitedError,
    ServerBusyError,
    TimeoutError,
    UnsupportedTypeError,
    register_error_handlers,
)


def create_error_test_app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/test-large")
    def raise_large():
        raise FileTooLargeError()

    @app.get("/test-unsupported")
    def raise_unsupported():
        raise UnsupportedTypeError()

    @app.get("/test-password")
    def raise_password():
        raise PasswordProtectedError()

    @app.get("/test-daily-limit")
    def raise_daily():
        raise DailyLimitError()

    @app.get("/test-rate-limit")
    def raise_rate():
        raise RateLimitedError()

    @app.get("/test-busy")
    def raise_busy():
        raise ServerBusyError()

    @app.get("/test-timeout")
    def raise_timeout():
        raise TimeoutError()

    @app.get("/test-crash")
    def raise_crash():
        raise RuntimeError("Unforeseen crash!")

    return app


def test_file_too_large_error_format():
    client = TestClient(create_error_test_app())
    res = client.get("/test-large")
    assert res.status_code == 413
    assert res.json() == {
        "code": "FILE_TOO_LARGE",
        "message": "This file is larger than the limit shown on this page. Try a smaller file",
    }


def test_unsupported_type_error_format():
    client = TestClient(create_error_test_app())
    res = client.get("/test-unsupported")
    assert res.status_code == 415
    assert res.json()["code"] == "UNSUPPORTED_TYPE"


def test_password_protected_error_format():
    client = TestClient(create_error_test_app())
    res = client.get("/test-password")
    assert res.status_code == 422
    assert res.json() == {
        "code": "PASSWORD_PROTECTED",
        "message": "This PDF is password protected. Remove the password and try again",
    }


def test_server_busy_error_format_and_headers():
    client = TestClient(create_error_test_app())
    res = client.get("/test-busy")
    assert res.status_code == 503
    assert res.headers.get("retry-after") == "10"
    assert res.json() == {
        "code": "SERVER_BUSY",
        "message": "The tool is busy right now. Please try again in a moment",
    }


def test_timeout_error_format():
    client = TestClient(create_error_test_app())
    res = client.get("/test-timeout")
    assert res.status_code == 504
    assert res.json()["code"] == "TIMEOUT"


def test_daily_limit_and_rate_limit_formats():
    client = TestClient(create_error_test_app())
    res_daily = client.get("/test-daily-limit")
    assert res_daily.status_code == 429
    assert res_daily.json()["code"] == "DAILY_LIMIT"

    res_rate = client.get("/test-rate-limit")
    assert res_rate.status_code == 429
    assert res_rate.json()["code"] == "RATE_LIMITED"


def test_unexpected_crash_masks_internal_details():
    client = TestClient(create_error_test_app(), raise_server_exceptions=False)
    res = client.get("/test-crash")
    assert res.status_code == 500
    assert res.json() == {
        "code": "SERVER_ERROR",
        "message": "Something went wrong on our side. Please try again",
    }
    # Ensure raw exception text is NOT leaked
    assert "Unforeseen crash!" not in res.text
