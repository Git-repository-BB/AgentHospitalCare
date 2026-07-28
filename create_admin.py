"""One-off CLI helper to create (or promote) an administrator user.

Usage:
    python create_admin.py <username> <password>

If the username already exists, its role is updated to "administrator"
and its password is left unchanged. Otherwise a new administrator
account is created with the given username/password.
"""
from __future__ import annotations

import sys

from app.auth.security import hash_password
from app.database.db import SessionLocal, init_db
from app.database.models import User


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <username> <password>")
        raise SystemExit(1)

    username, password = sys.argv[1], sys.argv[2]

    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is not None:
            user.role = "administrator"
            db.commit()
            print(f"Existing user '{username}' promoted to administrator.")
        else:
            user = User(username=username, hashed_password=hash_password(password), role="administrator")
            db.add(user)
            db.commit()
            print(f"Created new administrator user '{username}'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()