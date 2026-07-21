"""Password hashing and JWT helpers.

Uses PBKDF2-HMAC-SHA256 for password hashing (stdlib only, no extra native
dependency) and PyJWT for signing/verifying access tokens.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import os
import secrets

import jwt

JWT_SECRET = os.environ.get("AGENTCARE_JWT_SECRET", "dev-insecure-secret-change-me-please-32bytes")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("AGENTCARE_JWT_EXPIRE_MINUTES", "480"))

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


def create_access_token(subject: str, role: str) -> str:
    """Create a signed JWT access token for the given username/role."""
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + dt.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
