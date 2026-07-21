"""Administrator-only routes: audit log and escalation review."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.db import get_db
from app.services import audit_service, escalation_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("administrator"))])


@router.get("/escalations")
def list_escalations(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": e.id,
            "patient_id": e.patient_id,
            "request_text": e.request_text,
            "reason": e.reason,
            "resolved": e.resolved,
            "created_at": e.created_at.isoformat(),
        }
        for e in escalation_service.list_escalations(db)
    ]


@router.post("/escalations/{escalation_id}/resolve")
def resolve_escalation(escalation_id: int, db: Session = Depends(get_db)) -> dict:
    escalation = escalation_service.resolve_escalation(db, escalation_id)
    if escalation is None:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return {"id": escalation.id, "resolved": escalation.resolved}


@router.get("/audit-logs")
def list_audit_logs(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": a.id,
            "actor": a.actor,
            "action": a.action,
            "details": a.details,
            "created_at": a.created_at.isoformat(),
        }
        for a in audit_service.list_audit_logs(db)
    ]
