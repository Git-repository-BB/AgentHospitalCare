"""Request/response schemas for the workflow API."""
from __future__ import annotations

from pydantic import BaseModel, Field


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


class WorkflowStepFlags(BaseModel):
    needs_registration: bool = False
    needs_appointment: bool = False
    needs_documents: bool = False
    needs_reminder: bool = False
    is_unsafe: bool = False
    safety_reason: str = ""


class WorkflowStepResponse(BaseModel):
    session_id: str
    next_step: str
    last_step: str | None = None
    last_step_detail: str = ""
    finished: bool = False
    message: str = ""
    result: WorkflowResponse
    flags: WorkflowStepFlags = Field(default_factory=WorkflowStepFlags)


class WorkflowNextRequest(BaseModel):
    session_id: str
