"""Coordinator agent: interprets patient intent and produces an execution plan."""
from __future__ import annotations

from crewai import Agent

from app.prompts.agent_prompts import COORDINATOR_PROMPT


def build_coordinator_agent(llm) -> Agent:
    return Agent(
        role=COORDINATOR_PROMPT["role"],
        goal=COORDINATOR_PROMPT["goal"],
        backstory=COORDINATOR_PROMPT["backstory"],
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )
