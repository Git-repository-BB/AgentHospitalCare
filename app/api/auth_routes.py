"""Authentication routes: registration, login, and one-time admin bootstrap."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, hash_password, verify_password
from app.database.db import get_db
from app.database.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Public self-registration. Always creates a 'patient' role account."""
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    user = User(username=payload.username, hashed_password=hash_password(payload.password), role="patient")
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.username, role=user.role)
    return TokenResponse(access_token=token, role=user.role)


@router.post("/bootstrap-admin", response_model=TokenResponse)
def bootstrap_admin(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Create the first administrator account. Only works while no users exist yet."""
    if db.query(User).count() > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin bootstrap is only available before any accounts exist.",
        )

    user = User(username=payload.username, hashed_password=hash_password(payload.password), role="administrator")
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.username, role=user.role)
    return TokenResponse(access_token=token, role=user.role)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(subject=user.username, role=user.role)
    return TokenResponse(access_token=token, role=user.role)
