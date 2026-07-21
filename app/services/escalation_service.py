"""Safety escalation records for requests that require human/clinical review."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.models import Escalation


def create_escalation(db: Session, patient_id: str | None, request_text: str, reason: str) -> Escalation:
    escalation = Escalation(patient_id=patient_id, request_text=request_text, reason=reason, resolved=False)
    db.add(escalation)
    db.commit()
    db.refresh(escalation)
    return escalation


def list_escalations(db: Session, resolved: bool | None = None) -> list[Escalation]:
    query = db.query(Escalation)
    if resolved is not None:
        query = query.filter(Escalation.resolved == resolved)
    return query.order_by(Escalation.created_at.desc()).all()


def resolve_escalation(db: Session, escalation_id: int) -> Escalation | None:
    escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if escalation is None:
        return None
    escalation.resolved = True
    db.commit()
    return escalation
