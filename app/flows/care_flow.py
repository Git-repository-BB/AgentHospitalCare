"""CrewAI Flow orchestrating the non-clinical patient administration workflow.

Sequence: coordinate -> check_safety -> (escalate | proceed) -> route_department
-> handle_appointment -> handle_documents -> handle_followup -> finalize.

Each agentic step runs a single-agent, single-task Crew with a structured
(Pydantic) output so the flow can deterministically read the result back into
shared state, while the agent itself reasons with the LLM and calls tools.
"""
from __future__ import annotations

from typing import Any

from crewai import Crew, Process, Task
from crewai.flow.flow import Flow, listen, router, start
from pydantic import BaseModel, Field

from app.agents.appointment_agent import build_appointment_agent
from app.agents.coordinator_agent import build_coordinator_agent
from app.agents.document_agent import build_document_agent
from app.agents.followup_agent import build_followup_agent
from app.agents.routing_agent import build_routing_agent
from app.agents.safety_agent import build_safety_agent
from app.database.db import SessionLocal
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


class CareFlowState(BaseModel):
    request_text: str = ""
    patient_id: str | None = None

    intent: str | None = None
    needs_registration: bool = False
    needs_appointment: bool = False
    needs_documents: bool = False
    needs_reminder: bool = False

    is_unsafe: bool = False
    safety_reason: str = ""

    department_id: str | None = None
    department_name: str | None = None

    appointment_id: str | None = None
    appointment_time: str | None = None
    appointment_action: str | None = None

    pending_document_paths: list[str] = Field(default_factory=list)
    documents: list[str] = Field(default_factory=list)

    workflow_status: str = "RUNNING"
    escalated: bool = False
    steps: list[str] = Field(default_factory=list)
    agent_plan: list[str] = Field(default_factory=list)
    summary: str = ""


def _run_single_agent_task(agent, description: str, expected_output: str, output_pydantic):
    task = Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        output_pydantic=output_pydantic,
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff()
    return result.pydantic


class CareFlow(Flow[CareFlowState]):
    """Multi-agent flow for AgentCare's non-clinical patient administration requests."""

    @start()
    def coordinate(self):
        llm = get_llm()
        agent = build_coordinator_agent(llm)
        plan: CoordinatorPlan = _run_single_agent_task(
            agent,
            description=(
                "Analyze the following patient administrative request and determine the intent "
                "and which steps are needed. A request to cancel an appointment is an appointment "
                "scheduling request: set needs_appointment=True and use intent='appointment_cancellation'."
                f"\n\nRequest: \"{self.state.request_text}\""
            ),
            expected_output="A structured plan describing intent and required steps.",
            output_pydantic=CoordinatorPlan,
        )
        self.state.intent = plan.intent
        self.state.needs_registration = plan.needs_registration
        self.state.needs_appointment = plan.needs_appointment
        self.state.needs_documents = plan.needs_documents
        self.state.needs_reminder = plan.needs_reminder
        self.state.agent_plan.append("coordinator")

    @listen(coordinate)
    def check_safety(self):
        llm = get_llm()
        agent = build_safety_agent(llm)
        assessment: SafetyAssessment = _run_single_agent_task(
            agent,
            description=(
                "Assess whether the following patient request is asking for medical diagnosis, "
                "treatment, prescriptions, or other clinical advice this administrative system "
                "must not provide. If it is unsafe, call the Escalation Tool with "
                f"patient_id='{self.state.patient_id or ''}', the request text, and your reason, "
                "then call the Audit Tool with actor='safety_agent', action='safety_escalation', "
                f"and details describing why.\n\nRequest: \"{self.state.request_text}\""
            ),
            expected_output="A safety assessment with is_unsafe and reason.",
            output_pydantic=SafetyAssessment,
        )
        self.state.is_unsafe = assessment.is_unsafe
        self.state.safety_reason = assessment.reason
        self.state.agent_plan.append("safety")

    @router(check_safety)
    def route_after_safety(self):
        return "escalate" if self.state.is_unsafe else "proceed"

    @listen("escalate")
    def handle_escalation(self):
        self.state.workflow_status = "ESCALATED"
        self.state.escalated = True
        self.state.steps = ["safety_escalation"]
        self.state.summary = (
            f"Request escalated for human clinical review: {self.state.safety_reason}"
        )
        self._persist()
        return self._result()

    @listen("proceed")
    def route_department(self):
        llm = get_llm()
        agent = build_routing_agent(llm)
        decision: RoutingDecision = _run_single_agent_task(
            agent,
            description=(
                "Use the Department Lookup Tool to determine which hospital department should "
                f"handle this request.\n\nRequest: \"{self.state.request_text}\""
            ),
            expected_output="The department code and name from the tool.",
            output_pydantic=RoutingDecision,
        )
        self.state.department_id = decision.department_code
        self.state.department_name = decision.department_name
        self.state.agent_plan.append("routing")

        if self.state.needs_registration:
            db = SessionLocal()
            try:
                patient_service.get_or_create_patient(db, self.state.patient_id or "unknown")
            finally:
                db.close()
            self.state.steps.append("patient_registration")

    @listen(route_department)
    def handle_appointment(self):
        if not self.state.needs_appointment:
            return
        llm = get_llm()
        agent = build_appointment_agent(llm)
        result: AppointmentResult = _run_single_agent_task(
            agent,
            description=(
                f"Patient request: \"{self.state.request_text}\"\n\n"
                "Decide the required scheduling action. For booking, check availability with the "
                f"Appointment Availability Tool for department '{self.state.department_id}', then book "
                f"using patient_id='{self.state.patient_id or 'unknown'}' and "
                f"department_code='{self.state.department_id}'. For cancellation, extract the appointment "
                "id from the patient request and call the Appointment Cancellation Tool. Do not check "
                "availability or book a replacement when cancelling. If no numeric appointment id is "
                "provided, return action='failed' without calling a booking tool."
            ),
            expected_output="A structured result with action 'booked', 'cancelled', or 'failed', the appointment id, and detail.",
            output_pydantic=AppointmentResult,
        )
        self.state.agent_plan.append("appointment")
        self.state.appointment_action = result.action
        if result.action == "booked":
            self.state.appointment_id = result.appointment_id
            self.state.appointment_time = result.scheduled_time
            self.state.steps.append("appointment_booking")
        elif result.action == "cancelled":
            self.state.appointment_id = result.appointment_id
            self.state.steps.append("appointment_cancellation")

    @listen(handle_appointment)
    def handle_documents(self):
        if not self.state.needs_documents or not self.state.pending_document_paths:
            return
        llm = get_llm()
        agent = build_document_agent(llm)
        for path in self.state.pending_document_paths:
            result: DocumentResult = _run_single_agent_task(
                agent,
                description=(
                    "Check whether this file is a duplicate with the Duplicate Detection Tool "
                    f"using patient_id='{self.state.patient_id or 'unknown'}' and file_path='{path}'. "
                    "Then store it with the Document Storage Tool and summarize its metadata with "
                    "the Document Parser Tool."
                ),
                expected_output="Whether the document was stored, its id, and duplicate status.",
                output_pydantic=DocumentResult,
            )
            if result.stored and result.document_id:
                self.state.documents.append(result.document_id)
        self.state.agent_plan.append("document")
        self.state.steps.append("document_upload")

    @listen(handle_documents)
    def handle_followup(self):
        if not (self.state.needs_reminder or self.state.appointment_action == "booked"):
            return
        llm = get_llm()
        agent = build_followup_agent(llm)
        message = (
            f"Reminder: you have an upcoming appointment in {self.state.department_name}."
            if self.state.appointment_id
            else "Reminder: please follow up on your recent request."
        )
        remind_at = self.state.appointment_time or "tomorrow"
        result: FollowUpResult = _run_single_agent_task(
            agent,
            description=(
                f"Schedule a reminder for patient_id='{self.state.patient_id or 'unknown'}' with "
                f"message='{message}' using the Reminder Tool. Use remind_at_iso derived from "
                f"'{remind_at}' (use a sensible near-future ISO-8601 timestamp if it is not already "
                "one). Then send an immediate acknowledgement with the Notification Tool."
            ),
            expected_output="Whether a reminder was scheduled and its id.",
            output_pydantic=FollowUpResult,
        )
        self.state.agent_plan.append("follow_up")
        if result.reminder_scheduled:
            self.state.steps.append("reminder_schedule")

    @listen(handle_followup)
    def finalize(self):
        if not self.state.steps:
            self.state.steps.append("general_assistance")
        self.state.workflow_status = "COMPLETED"
        self.state.summary = (
            f"Request routed to {self.state.department_id} for administrative handling."
        )
        self._persist()
        return self._result()

    def _persist(self) -> None:
        db = SessionLocal()
        try:
            workflow_service.save_workflow_run(db, self._result())
        finally:
            db.close()

    def _result(self) -> dict[str, Any]:
        return {
            "patient_id": self.state.patient_id,
            "department_id": self.state.department_id,
            "appointment_id": self.state.appointment_id,
            "documents": self.state.documents,
            "workflow_status": self.state.workflow_status,
            "escalated": self.state.escalated,
            "steps": self.state.steps,
            "summary": self.state.summary,
            "intent": self.state.intent,
            "agent_plan": self.state.agent_plan,
        }


def run_care_flow(request_text: str, patient_id: str | None = None, document_paths: list[str] | None = None) -> dict[str, Any]:
    """Convenience entry point: run the flow end-to-end and return the final result dict."""
    flow = CareFlow()
    flow.kickoff(
        inputs={
            "request_text": request_text,
            "patient_id": patient_id,
            "pending_document_paths": document_paths or [],
        }
    )
    return flow._result()
