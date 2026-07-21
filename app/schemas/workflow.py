"""Request/response schemas for the workflow API."""
from __future__ import annotations

from pydantic import BaseModel


class PatientRequest(BaseModel):
    patient_id: str | None = None
    request_text: str


class WorkflowResponse(BaseModel):
    patient_id: str | None
    department_id: str | None
    appointment_id: str | None
    documents: list[str]
    workflow_status: str
    escalated: bool
    steps: list[str]
    summary: str
    intent: str | None = None
    agent_plan: list[str] = []
