"""Follow-up agent: schedules reminders and notifies patients."""
from __future__ import annotations

from crewai import Agent

from app.prompts.agent_prompts import FOLLOWUP_PROMPT
from app.tools.reminder_tools import notification_tool, reminder_tool


def build_followup_agent(llm) -> Agent:
    return Agent(
        role=FOLLOWUP_PROMPT["role"],
        goal=FOLLOWUP_PROMPT["goal"],
        backstory=FOLLOWUP_PROMPT["backstory"],
        tools=[reminder_tool, notification_tool],
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )
