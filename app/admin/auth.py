"""SQLAdmin Authentication Backend with Argon2 verification and login rate limiting."""

import time
import uuid

from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request

from app.db import get_session_factory
from app.models.admin_user import AdminUser
from app.security import verify_password

# In-memory tracking for failed login attempts to throttle brute force attacks
# { ip_address: {"count": int, "blocked_until": float} }
_failed_login_attempts: dict[str, dict[str, float]] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 300.0  # 5 minutes lockout after 5 failed attempts


class AdminAuth(AuthenticationBackend):
    """Secure authentication handler for SQLAdmin panel."""

    def __init__(self, secret_key: str, session_factory=None) -> None:
        super().__init__(secret_key=secret_key)
        self.session_factory = session_factory or get_session_factory()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address safely for login rate limiting."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "127.0.0.1"

    def _is_rate_limited(self, ip: str) -> bool:
        """Check if an IP is currently blocked due to repeated failed logins."""
        now = time.monotonic()
        record = _failed_login_attempts.get(ip)
        if not record:
            return False
        if record.get("blocked_until", 0) > now:
            return True
        if record.get("blocked_until", 0) <= now and record.get("count", 0) >= MAX_FAILED_ATTEMPTS:
            # Lockout expired, reset counter
            _failed_login_attempts.pop(ip, None)
            return False
        return False

    def _record_failed_attempt(self, ip: str) -> None:
        """Increment failed attempts and apply temporary lockout if threshold is exceeded."""
        now = time.monotonic()
        if ip not in _failed_login_attempts:
            _failed_login_attempts[ip] = {"count": 0, "blocked_until": 0}
        _failed_login_attempts[ip]["count"] += 1
        if _failed_login_attempts[ip]["count"] >= MAX_FAILED_ATTEMPTS:
            _failed_login_attempts[ip]["blocked_until"] = now + LOCKOUT_DURATION_SECONDS

    def _clear_failed_attempts(self, ip: str) -> None:
        """Reset failed attempt counters upon successful authentication."""
        _failed_login_attempts.pop(ip, None)

    async def login(self, request: Request) -> bool:
        """Process admin login form submission."""
        ip = self._get_client_ip(request)
        if self._is_rate_limited(ip):
            return False

        form = await request.form()
        # SQLAdmin login form defaults to "username" for the identity field
        email = str(form.get("username") or form.get("email") or "").strip().lower()
        password = str(form.get("password") or "")

        if not email or not password:
            self._record_failed_attempt(ip)
            return False

        with self.session_factory() as session:
            user = session.scalar(select(AdminUser).where(AdminUser.email == email))
            if not user or not user.is_active:
                self._record_failed_attempt(ip)
                return False

            if not verify_password(user.password_hash, password):
                self._record_failed_attempt(ip)
                return False

            # Login successful: clear failure tracking and store signed session state
            self._clear_failed_attempts(ip)
            request.session.update({
                "token": str(user.id),
                "admin_email": user.email,
                "login_time": time.time(),
            })
            return True

    async def logout(self, request: Request) -> bool:
        """Clear signed session state on logout."""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """Verify that the current request possesses a valid active admin session."""
        user_id_str = request.session.get("token")
        if not user_id_str:
            return False

        try:
            user_uuid = uuid.UUID(user_id_str)
        except (ValueError, TypeError):
            request.session.clear()
            return False

        with self.session_factory() as session:
            user = session.scalar(select(AdminUser).where(AdminUser.id == user_uuid))
            if not user or not user.is_active:
                request.session.clear()
                return False

            return True

    @staticmethod
    def reset_rate_limits() -> None:
        """Reset all in-memory rate-limiting counters (for testing)."""
        _failed_login_attempts.clear()
