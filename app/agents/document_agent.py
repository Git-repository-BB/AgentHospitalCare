"""Document agent: parses, stores, and de-duplicates uploaded patient documents."""
from __future__ import annotations

from crewai import Agent

from app.prompts.agent_prompts import DOCUMENT_PROMPT
from app.tools.document_tools import document_parser_tool, document_storage_tool, duplicate_detection_tool


def build_document_agent(llm) -> Agent:
    return Agent(
        role=DOCUMENT_PROMPT["role"],
        goal=DOCUMENT_PROMPT["goal"],
        backstory=DOCUMENT_PROMPT["backstory"],
        tools=[document_parser_tool, document_storage_tool, duplicate_detection_tool],
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )
