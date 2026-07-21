"""Tools the Follow-up Agent uses to schedule reminders and notify patients."""
from __future__ import annotations

import datetime as dt

from crewai.tools import tool

from app.database.db import SessionLocal
from app.services import reminder_service


@tool("Reminder Tool")
def reminder_tool(patient_id: str, message: str, remind_at_iso: str) -> str:
    """Schedule a reminder for a patient at a future point in time.

    Args:
        patient_id: Identifier of the patient to remind.
        message: The reminder message to send.
        remind_at_iso: ISO-8601 timestamp of when the reminder should fire.

    Returns:
        A string "reminder_id|remind_at" describing the scheduled reminder.
    """
    db = SessionLocal()
    try:
        remind_at = dt.datetime.fromisoformat(remind_at_iso)
        reminder = reminder_service.schedule_reminder(db, patient_id, message, remind_at)
        return f"{reminder.id}|{reminder.remind_at.isoformat()}"
    finally:
        db.close()


@tool("Notification Tool")
def notification_tool(patient_id: str, message: str) -> str:
    """Send an immediate notification to a patient (logged in this prototype).

    Args:
        patient_id: Identifier of the patient to notify.
        message: The notification message.

    Returns:
        A confirmation string.
    """
    result = reminder_service.send_notification(patient_id, message)
    return f"notified:{result['status']}"
