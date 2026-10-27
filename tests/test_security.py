"""Tests for password hashing and verification using Argon2."""

import pytest

from app.security import hash_password, verify_password


def test_argon2_hashing_and_verification():
    """Verify that password can be hashed and verified with Argon2."""
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed.startswith("$argon2id$")
    assert verify_password(hashed, password) is True
    assert verify_password(hashed, "WrongPassword") is False


def test_empty_password_rejected():
    """Verify empty or blank password raises ValueError."""
    with pytest.raises(ValueError, match="Password cannot be empty"):
        hash_password("")

    with pytest.raises(ValueError, match="Password cannot be empty"):
        hash_password("   ")
