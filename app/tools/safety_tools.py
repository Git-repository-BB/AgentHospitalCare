"""Tools the Safety Agent uses to escalate unsafe requests and record audit trail entries."""
from __future__ import annotations

from crewai.tools import tool

from app.database.db import SessionLocal
from app.services import audit_service, escalation_service


@tool("Escalation Tool")
def escalation_tool(patient_id: str, request_text: str, reason: str) -> str:
    """Record a safety escalation for a request that needs human/clinical review.

    Args:
        patient_id: Identifier of the patient who made the request (may be empty).
        request_text: The original request text.
        reason: Why the request was flagged as unsafe.

    Returns:
        A string "escalation_id" confirming the record was stored.
    """
    db = SessionLocal()
    try:
        escalation = escalation_service.create_escalation(db, patient_id or None, request_text, reason)
        return str(escalation.id)
    finally:
        db.close()


@tool("Audit Tool")
def audit_tool(actor: str, action: str, details: str) -> str:
    """Record an audit log entry for an agent or user action.

    Args:
        actor: Who/what performed the action (e.g. "safety_agent").
        action: A short action name (e.g. "escalated_request").
        details: Additional free-text context.

    Returns:
        A string "audit_id" confirming the record was stored.
    """
    db = SessionLocal()
    try:
        entry = audit_service.log_action(db, actor, action, details)
        return str(entry.id)
    finally:
        db.close()
