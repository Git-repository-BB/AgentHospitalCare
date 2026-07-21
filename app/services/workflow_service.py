"""Persistence for completed/escalated workflow runs (replaces the old app/database.py)."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.database.models import WorkflowRun


def save_workflow_run(db: Session, payload: dict[str, Any]) -> WorkflowRun:
    run = WorkflowRun(
        patient_id=payload.get("patient_id"),
        department_id=payload.get("department_id"),
        appointment_id=payload.get("appointment_id"),
        workflow_status=payload.get("workflow_status", "COMPLETED"),
        escalated=bool(payload.get("escalated", False)),
        intent=payload.get("intent"),
        agent_plan=";".join(payload.get("agent_plan", [])),
        summary=payload.get("summary", ""),
        steps="|".join(payload.get("steps", [])),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def list_workflow_runs(db: Session) -> list[dict[str, Any]]:
    rows = db.query(WorkflowRun).order_by(WorkflowRun.id.desc()).all()
    return [
        {
            "id": row.id,
            "patient_id": row.patient_id,
            "department_id": row.department_id,
            "appointment_id": row.appointment_id,
            "workflow_status": row.workflow_status,
            "escalated": row.escalated,
            "intent": row.intent,
            "agent_plan": row.agent_plan.split(";") if row.agent_plan else [],
            "summary": row.summary,
            "steps": row.steps.split("|") if row.steps else [],
        }
        for row in rows
    ]
