import jwt
import pytest

from app.auth.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_and_verify_password_round_trip() -> None:
    hashed = hash_password("correct-horse-battery-staple")

    assert verify_password("correct-horse-battery-staple", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_hash_password_uses_random_salt() -> None:
    assert hash_password("same-password") != hash_password("same-password")


def test_access_token_round_trip() -> None:
    token = create_access_token(subject="alice", role="patient")

    payload = decode_access_token(token)

    assert payload["sub"] == "alice"
    assert payload["role"] == "patient"


def test_decode_invalid_token_raises() -> None:
    with pytest.raises(jwt.PyJWTError):
        decode_access_token("not-a-real-token")
