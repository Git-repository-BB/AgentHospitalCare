from app.auth.security import hash_password, verify_password


def test_hash_and_verify_password_round_trip() -> None:
    hashed = hash_password("correct-horse-battery-staple")

    assert verify_password("correct-horse-battery-staple", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_hash_password_uses_random_salt() -> None:
    assert hash_password("same-password") != hash_password("same-password")
