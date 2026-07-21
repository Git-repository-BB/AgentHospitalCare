"""Safety agent: gates requests that ask for medical advice/diagnosis/treatment."""
from __future__ import annotations

from crewai import Agent

from app.prompts.agent_prompts import SAFETY_PROMPT
from app.tools.safety_tools import audit_tool, escalation_tool


def build_safety_agent(llm) -> Agent:
    return Agent(
        role=SAFETY_PROMPT["role"],
        goal=SAFETY_PROMPT["goal"],
        backstory=SAFETY_PROMPT["backstory"],
        tools=[escalation_tool, audit_tool],
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )
