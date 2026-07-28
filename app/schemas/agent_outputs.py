"""Pydantic schemas for structured LLM task outputs within the CrewAI flow."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CoordinatorPlan(BaseModel):
    intent: str = Field(description="Short intent label, e.g. 'cardiology', 'registration', 'appointment_booking', or 'appointment_cancellation'.")
    needs_registration: bool = Field(description="Whether the patient needs to be registered.")
    needs_appointment: bool = Field(description="Whether the request needs appointment scheduling, including booking or cancellation.")
    needs_documents: bool = Field(description="Whether the request involves document upload/handling.")
    needs_reminder: bool = Field(description="Whether the patient wants a follow-up reminder.")


class SafetyAssessment(BaseModel):
    is_unsafe: bool = Field(description="True if the request asks for diagnosis, treatment, or prescriptions.")
    reason: str = Field(description="Brief explanation of the safety determination.")


class RoutingDecision(BaseModel):
    department_code: str = Field(description="The department code returned by the lookup tool.")
    department_name: str = Field(description="The human-readable department name.")


class AppointmentResult(BaseModel):
    action: Literal["booked", "cancelled", "failed"] = Field(description="The scheduling action completed by the appointment tools.")
    appointment_id: str | None = Field(default=None, description="The appointment id that was booked or cancelled, if any.")
    scheduled_time: str | None = Field(default=None, description="ISO timestamp of the booked slot, if any.")
    detail: str = Field(default="", description="Any extra detail or error message from the tool.")


class DocumentResult(BaseModel):
    stored: bool = Field(description="Whether the document was stored.")
    document_id: str | None = Field(default=None)
    is_duplicate: bool = Field(default=False)
    detail: str = Field(default="")


class FollowUpResult(BaseModel):
    reminder_scheduled: bool = Field(description="Whether a reminder was scheduled.")
    reminder_id: str | None = Field(default=None)
    detail: str = Field(default="")
