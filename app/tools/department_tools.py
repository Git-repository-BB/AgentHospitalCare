"""Tool the Routing Agent uses to map free-text requests to hospital departments."""
from __future__ import annotations

from crewai.tools import tool

from app.database.db import SessionLocal
from app.services import department_service


@tool("Department Lookup Tool")
def department_lookup_tool(request_text: str) -> str:
    """Look up which hospital department best matches a patient's request text.

    Args:
        request_text: The patient's free-text request describing what they need.

    Returns:
        A string in the form "code|name" for the best-matching department.
    """
    db = SessionLocal()
    try:
        department_service.seed_departments(db)
        department = department_service.lookup_department(db, request_text)
        return f"{department.code}|{department.name}"
    finally:
        db.close()
