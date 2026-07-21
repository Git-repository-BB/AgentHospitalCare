"""Reminder scheduling (APScheduler) and patient notifications."""
from __future__ import annotations

import datetime as dt
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.database.models import Reminder

logger = logging.getLogger("agentcare.reminders")

_scheduler: BackgroundScheduler | None = None


def _get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
        _scheduler.start()
    return _scheduler


def _mark_reminder_sent(reminder_id: int) -> None:
    db = SessionLocal()
    try:
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder is not None:
            reminder.sent = True
            db.commit()
            send_notification(reminder.patient_id, reminder.message)
    finally:
        db.close()


def schedule_reminder(
    db: Session,
    patient_id: str,
    message: str,
    remind_at: dt.datetime,
    appointment_id: int | None = None,
) -> Reminder:
    """Persist a reminder and schedule a background job to fire it at remind_at."""
    reminder = Reminder(
        patient_id=patient_id,
        appointment_id=appointment_id,
        remind_at=remind_at,
        message=message,
        sent=False,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    scheduler = _get_scheduler()
    run_date = remind_at if remind_at.tzinfo else remind_at.replace(tzinfo=dt.timezone.utc)
    scheduler.add_job(
        _mark_reminder_sent,
        trigger="date",
        run_date=run_date,
        args=[reminder.id],
        id=f"reminder-{reminder.id}",
        replace_existing=True,
    )
    return reminder


def send_notification(patient_id: str, message: str) -> dict:
    """Send a patient notification. In this prototype, logs the message (no real SMS/email)."""
    logger.info("Notification for patient %s: %s", patient_id, message)
    return {"patient_id": patient_id, "message": message, "status": "logged"}


def list_reminders(db: Session, patient_id: str) -> list[Reminder]:
    return db.query(Reminder).filter(Reminder.patient_id == patient_id).all()
