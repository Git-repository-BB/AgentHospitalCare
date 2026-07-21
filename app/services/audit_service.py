"""Append-only audit trail of agent and user actions."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.models import AuditLog


def log_action(db: Session, actor: str, action: str, details: str = "") -> AuditLog:
    entry = AuditLog(actor=actor, action=action, details=details)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_audit_logs(db: Session) -> list[AuditLog]:
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()
