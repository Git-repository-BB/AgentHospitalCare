import datetime as dt

from app.services import reminder_service


def test_schedule_reminder_persists_row(db_session) -> None:
    remind_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)

    reminder = reminder_service.schedule_reminder(db_session, "patient-1", "Don't forget your appointment", remind_at)

    assert reminder.id is not None
    assert reminder.patient_id == "patient-1"
    assert reminder.sent is False


def test_send_notification_returns_logged_status() -> None:
    result = reminder_service.send_notification("patient-1", "hello")

    assert result == {"patient_id": "patient-1", "message": "hello", "status": "logged"}
