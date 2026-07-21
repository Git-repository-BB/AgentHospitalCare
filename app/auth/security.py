"""Password hashing helpers.

Uses PBKDF2-HMAC-SHA256 for password hashing (stdlib only, no extra native
dependency). Authentication itself is username + password via HTTP Basic Auth.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

_PBKDF2_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    """Hash a password with a random salt using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a stored salt$hash value."""
    try:
        salt_b64, hash_b64 = hashed.split("$", 1)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
    except (ValueError, Exception):
        return False
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return hmac.compare_digest(derived, expected)
