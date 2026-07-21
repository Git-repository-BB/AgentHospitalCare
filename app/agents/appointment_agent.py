"""Appointment agent: checks availability and books appointments via tools."""
from __future__ import annotations

from crewai import Agent

from app.prompts.agent_prompts import APPOINTMENT_PROMPT
from app.tools.appointment_tools import (
    appointment_availability_tool,
    appointment_booking_tool,
    appointment_cancellation_tool,
)


def build_appointment_agent(llm) -> Agent:
    return Agent(
        role=APPOINTMENT_PROMPT["role"],
        goal=APPOINTMENT_PROMPT["goal"],
        backstory=APPOINTMENT_PROMPT["backstory"],
        tools=[appointment_availability_tool, appointment_booking_tool, appointment_cancellation_tool],
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )
