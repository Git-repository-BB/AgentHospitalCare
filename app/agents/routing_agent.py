"""Routing agent: determines which hospital department handles a request."""
from __future__ import annotations

from crewai import Agent

from app.prompts.agent_prompts import ROUTING_PROMPT
from app.tools.department_tools import department_lookup_tool


def build_routing_agent(llm) -> Agent:
    return Agent(
        role=ROUTING_PROMPT["role"],
        goal=ROUTING_PROMPT["goal"],
        backstory=ROUTING_PROMPT["backstory"],
        tools=[department_lookup_tool],
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )
