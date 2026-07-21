"""Shared LLM factory for all CrewAI agents.

Reads configuration from environment variables (see .env.example):
- OPENAI_API_KEY: required for the default OpenAI-backed model.
- OPENAI_MODEL_NAME: optional override, defaults to "gpt-4o-mini".
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")


def get_llm(temperature: float = 0.2):
    """Build a crewai LLM instance. Raises a clear error if no API key is configured."""
    from crewai import LLM

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key "
            "before running agentic workflow requests."
        )
    return LLM(model=DEFAULT_MODEL, temperature=temperature)
