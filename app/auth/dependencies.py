"""FastAPI dependencies for authentication and role-based access control.

Uses HTTP Basic Auth: every protected request sends username + password.
No JWT tokens are issued or verified.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.auth.security import verify_password
from app.database.db import get_db
from app.database.models import User

security = HTTPBasic(auto_error=False)


def get_current_user(
    credentials: HTTPBasicCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password",
        headers={"WWW-Authenticate": "Basic"},
    )
    if credentials is None:
        raise credentials_error

    user = db.query(User).filter(User.username == credentials.username).first()
    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise credentials_error
    return user


def require_role(*allowed_roles: str):
    """Dependency factory that enforces the current user has one of the allowed roles."""

    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user

    return _check
