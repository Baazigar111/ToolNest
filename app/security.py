"""Security utilities: Argon2 password hashing and verification."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2."""
    if not password or not password.strip():
        raise ValueError("Password cannot be empty.")
    return _hasher.hash(password)


def verify_password(hash_value: str, password: str) -> bool:
    """Verify a password against an Argon2 hash. Returns True on success, False otherwise."""
    if not hash_value or not password:
        return False
    try:
        return _hasher.verify(hash_value, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
