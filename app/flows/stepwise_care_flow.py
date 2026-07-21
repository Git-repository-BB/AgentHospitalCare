"""Step-by-step CareFlow runner for interactive / Swagger testing.

Each call to ``advance_session`` runs exactly one agent (or terminal) step
and returns the updated state so the caller can inspect results before
continuing.
"""
from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel

from app.agents.appointment_agent import build_appointment_agent
from app.agents.coordinator_agent import build_coordinator_agent
from app.agents.document_agent import build_document_agent
from app.agents.followup_agent import build_followup_agent
from app.agents.routing_agent import build_routing_agent
from app.agents.safety_agent import build_safety_agent
from app.database.db import SessionLocal
from app.flows.care_flow import CareFlowState, _run_single_agent_task
from app.llm import get_llm
from app.schemas.agent_outputs import (
    AppointmentResult,
    CoordinatorPlan,
    DocumentResult,
    FollowUpResult,
    RoutingDecision,
    SafetyAssessment,
)
from app.services import patient_service, workflow_service

# Ordered pipeline labels shown to the client.
STEP_COORDINATOR = "coordinator"
STEP_SAFETY = "safety"
STEP_ESCALATE = "escalate"
STEP_ROUTING = "routing"
STEP_APPOINTMENT = "appointment"
STEP_DOCUMENTS = "documents"
STEP_FOLLOWUP = "followup"
STEP_FINALIZE = "finalize"
STEP_DONE = "done"


class StepSession(BaseModel):
    session_id: str
    state: CareFlowState
    next_step: str = STEP_COORDINATOR
    last_step: str | None = None
    last_step_detail: str = ""


_sessions: dict[str, StepSession] = {}


def start_session(
    request_text: str,
    patient_id: str | None = None,
    document_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new stepwise session. Does not run any agent yet."""
    session_id = str(uuid.uuid4())
    state = CareFlowState(
        request_text=request_text,
        patient_id=patient_id,
        pending_document_paths=document_paths or [],
        workflow_status="RUNNING",
    )
    session = StepSession(session_id=session_id, state=state, next_step=STEP_COORDINATOR)
    _sessions[session_id] = session
    return _session_payload(session, message="Session created. Call /workflow/next to run the coordinator step.")


def get_session(session_id: str) -> dict[str, Any] | None:
    session = _sessions.get(session_id)
    if session is None:
        return None
    return _session_payload(session, message="Current session state.")


def advance_session(session_id: str) -> dict[str, Any]:
    """Run exactly one pipeline step for the session."""
    session = _sessions.get(session_id)
    if session is None:
        raise KeyError(session_id)
    if session.next_step == STEP_DONE:
        return _session_payload(session, message="Workflow already finished. No further steps.")

    step = session.next_step
    detail = _run_step(session, step)
    session.last_step = step
    session.last_step_detail = detail
    return _session_payload(session, message=f"Ran step '{step}'. Next: '{session.next_step}'.")


def _run_step(session: StepSession, step: str) -> str:
    state = session.state
    llm = get_llm()

    if step == STEP_COORDINATOR:
        plan: CoordinatorPlan = _run_single_agent_task(
            build_coordinator_agent(llm),
            description=(
                "Analyze the following patient administrative request and determine the intent "
                f"and which steps are needed.\n\nRequest: \"{state.request_text}\""
            ),
            expected_output="A structured plan describing intent and required steps.",
            output_pydantic=CoordinatorPlan,
        )
        state.intent = plan.intent
        state.needs_registration = plan.needs_registration
        state.needs_appointment = plan.needs_appointment
        state.needs_documents = plan.needs_documents
        state.needs_reminder = plan.needs_reminder
        state.agent_plan.append("coordinator")
        session.next_step = STEP_SAFETY
        return f"intent={plan.intent}"

    if step == STEP_SAFETY:
        assessment: SafetyAssessment = _run_single_agent_task(
            build_safety_agent(llm),
            description=(
                "Assess whether the following patient request is asking for medical diagnosis, "
                "treatment, prescriptions, or other clinical advice this administrative system "
                "must not provide. If it is unsafe, call the Escalation Tool with "
                f"patient_id='{state.patient_id or ''}', the request text, and your reason, "
                "then call the Audit Tool with actor='safety_agent', action='safety_escalation', "
                f"and details describing why.\n\nRequest: \"{state.request_text}\""
            ),
            expected_output="A safety assessment with is_unsafe and reason.",
            output_pydantic=SafetyAssessment,
        )
        state.is_unsafe = assessment.is_unsafe
        state.safety_reason = assessment.reason
        state.agent_plan.append("safety")
        session.next_step = STEP_ESCALATE if assessment.is_unsafe else STEP_ROUTING
        return f"is_unsafe={assessment.is_unsafe}; reason={assessment.reason}"

    if step == STEP_ESCALATE:
        state.workflow_status = "ESCALATED"
        state.escalated = True
        state.steps = ["safety_escalation"]
        state.summary = f"Request escalated for human clinical review: {state.safety_reason}"
        _persist(state)
        session.next_step = STEP_DONE
        return state.summary

    if step == STEP_ROUTING:
        decision: RoutingDecision = _run_single_agent_task(
            build_routing_agent(llm),
            description=(
                "Use the Department Lookup Tool to determine which hospital department should "
                f"handle this request.\n\nRequest: \"{state.request_text}\""
            ),
            expected_output="The department code and name from the tool.",
            output_pydantic=RoutingDecision,
        )
        state.department_id = decision.department_code
        state.department_name = decision.department_name
        state.agent_plan.append("routing")
        if state.needs_registration:
            db = SessionLocal()
            try:
                patient_service.get_or_create_patient(db, state.patient_id or "unknown")
            finally:
                db.close()
            state.steps.append("patient_registration")
        session.next_step = STEP_APPOINTMENT
        return f"department={decision.department_code}"

    if step == STEP_APPOINTMENT:
        if not state.needs_appointment:
            session.next_step = STEP_DOCUMENTS
            return "skipped (needs_appointment=False)"
        result: AppointmentResult = _run_single_agent_task(
            build_appointment_agent(llm),
            description=(
                "Check availability with the Appointment Availability Tool for department "
                f"'{state.department_id}', then book the earliest slot with the Appointment "
                f"Booking Tool using patient_id='{state.patient_id or 'unknown'}' and "
                f"department_code='{state.department_id}'."
            ),
            expected_output="Whether an appointment was booked, its id and scheduled time.",
            output_pydantic=AppointmentResult,
        )
        state.agent_plan.append("appointment")
        if result.booked:
            state.appointment_id = result.appointment_id
            state.appointment_time = result.scheduled_time
            state.steps.append("appointment_booking")
        session.next_step = STEP_DOCUMENTS
        return f"booked={result.booked}; appointment_id={result.appointment_id}"

    if step == STEP_DOCUMENTS:
        if not state.needs_documents or not state.pending_document_paths:
            session.next_step = STEP_FOLLOWUP
            return "skipped (no documents pending)"
        for path in state.pending_document_paths:
            result: DocumentResult = _run_single_agent_task(
                build_document_agent(llm),
                description=(
                    "Check whether this file is a duplicate with the Duplicate Detection Tool "
                    f"using patient_id='{state.patient_id or 'unknown'}' and file_path='{path}'. "
                    "Then store it with the Document Storage Tool and summarize its metadata with "
                    "the Document Parser Tool."
                ),
                expected_output="Whether the document was stored, its id, and duplicate status.",
                output_pydantic=DocumentResult,
            )
            if result.stored and result.document_id:
                state.documents.append(result.document_id)
        state.agent_plan.append("document")
        state.steps.append("document_upload")
        session.next_step = STEP_FOLLOWUP
        return f"documents={state.documents}"

    if step == STEP_FOLLOWUP:
        if not (state.needs_reminder or state.appointment_id):
            session.next_step = STEP_FINALIZE
            return "skipped (no reminder needed)"
        message = (
            f"Reminder: you have an upcoming appointment in {state.department_name}."
            if state.appointment_id
            else "Reminder: please follow up on your recent request."
        )
        remind_at = state.appointment_time or "tomorrow"
        result: FollowUpResult = _run_single_agent_task(
            build_followup_agent(llm),
            description=(
                f"Schedule a reminder for patient_id='{state.patient_id or 'unknown'}' with "
                f"message='{message}' using the Reminder Tool. Use remind_at_iso derived from "
                f"'{remind_at}' (use a sensible near-future ISO-8601 timestamp if it is not already "
                "one). Then send an immediate acknowledgement with the Notification Tool."
            ),
            expected_output="Whether a reminder was scheduled and its id.",
            output_pydantic=FollowUpResult,
        )
        state.agent_plan.append("follow_up")
        if result.reminder_scheduled:
            state.steps.append("reminder_schedule")
        session.next_step = STEP_FINALIZE
        return f"reminder_scheduled={result.reminder_scheduled}"

    if step == STEP_FINALIZE:
        if not state.steps:
            state.steps.append("general_assistance")
        state.workflow_status = "COMPLETED"
        state.summary = f"Request routed to {state.department_id} for administrative handling."
        _persist(state)
        session.next_step = STEP_DONE
        return state.summary

    raise ValueError(f"Unknown step: {step}")


def _persist(state: CareFlowState) -> None:
    db = SessionLocal()
    try:
        workflow_service.save_workflow_run(db, _result_dict(state))
    finally:
        db.close()


def _result_dict(state: CareFlowState) -> dict[str, Any]:
    return {
        "patient_id": state.patient_id,
        "department_id": state.department_id,
        "appointment_id": state.appointment_id,
        "documents": list(state.documents),
        "workflow_status": state.workflow_status,
        "escalated": state.escalated,
        "steps": list(state.steps),
        "summary": state.summary,
        "intent": state.intent,
        "agent_plan": list(state.agent_plan),
    }


def _session_payload(session: StepSession, message: str) -> dict[str, Any]:
    return {
        "session_id": session.session_id,
        "next_step": session.next_step,
        "last_step": session.last_step,
        "last_step_detail": session.last_step_detail,
        "finished": session.next_step == STEP_DONE,
        "message": message,
        "result": _result_dict(session.state),
        "flags": {
            "needs_registration": session.state.needs_registration,
            "needs_appointment": session.state.needs_appointment,
            "needs_documents": session.state.needs_documents,
            "needs_reminder": session.state.needs_reminder,
            "is_unsafe": session.state.is_unsafe,
            "safety_reason": session.state.safety_reason,
        },
    }
