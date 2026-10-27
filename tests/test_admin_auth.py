"""Tests for AdminAuth backend and brute-force protection."""

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.admin.auth import MAX_FAILED_ATTEMPTS, AdminAuth
from app.models.admin_user import AdminUser
from app.security import hash_password


class MockRequest:
    """Mock Starlette Request for unit testing AdminAuth."""

    def __init__(self, form_data: dict, session: dict = None, ip: str = "127.0.0.1"):
        self._form = form_data
        self.session = session if session is not None else {}
        self.client = type("Client", (), {"host": ip})()
        self.headers = {}

    async def form(self):
        return self._form


@pytest.mark.anyio
async def test_admin_auth_success_and_logout(db_session: Session, sqlite_engine):
    """Test successful login sets session and logout clears it."""
    session_factory = sessionmaker(bind=sqlite_engine)
    auth = AdminAuth(secret_key="test-secret-key", session_factory=session_factory)
    AdminAuth.reset_rate_limits()

    # Create admin user
    user = AdminUser(
        email="testadmin@toolnest.example",
        password_hash=hash_password("SuperSecure123!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    req = MockRequest(form_data={"username": "testadmin@toolnest.example", "password": "SuperSecure123!"})
    login_success = await auth.login(req)
    assert login_success is True
    assert "token" in req.session
    assert req.session["token"] == str(user.id)

    # Authenticate request
    is_authenticated = await auth.authenticate(req)
    assert is_authenticated is True

    # Logout
    logout_success = await auth.logout(req)
    assert logout_success is True
    assert len(req.session) == 0


@pytest.mark.anyio
async def test_admin_auth_invalid_credentials_and_inactive(db_session: Session, sqlite_engine):
    """Test wrong password or inactive user is rejected."""
    session_factory = sessionmaker(bind=sqlite_engine)
    auth = AdminAuth(secret_key="test-secret-key", session_factory=session_factory)
    AdminAuth.reset_rate_limits()

    user = AdminUser(
        email="active@toolnest.example",
        password_hash=hash_password("ValidPassword123!"),
        is_active=False,  # Inactive user
    )
    db_session.add(user)
    db_session.commit()

    # Inactive user rejected
    req = MockRequest(form_data={"username": "active@toolnest.example", "password": "ValidPassword123!"})
    assert await auth.login(req) is False

    # Wrong password rejected
    req_wrong = MockRequest(form_data={"username": "active@toolnest.example", "password": "WrongPassword!"})
    assert await auth.login(req_wrong) is False


@pytest.mark.anyio
async def test_admin_auth_rate_limiting(db_session: Session, sqlite_engine):
    """Test that repeated failed attempts triggers rate limiting / lockout."""
    session_factory = sessionmaker(bind=sqlite_engine)
    auth = AdminAuth(secret_key="test-secret-key", session_factory=session_factory)
    AdminAuth.reset_rate_limits()

    test_ip = "192.168.1.50"
    for _ in range(MAX_FAILED_ATTEMPTS):
        req = MockRequest(
            form_data={"username": "nonexistent@toolnest.example", "password": "bad"},
            ip=test_ip,
        )
        assert await auth.login(req) is False

    # 6th attempt should be blocked by rate limit check
    blocked_req = MockRequest(
        form_data={"username": "nonexistent@toolnest.example", "password": "bad"},
        ip=test_ip,
    )
    assert await auth.login(blocked_req) is False
    assert auth._is_rate_limited(test_ip) is True
