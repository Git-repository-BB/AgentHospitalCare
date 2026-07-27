"""Clear appointment-related data so scheduling can start from an empty state."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.database.db import SessionLocal, init_db
from app.database.models import Appointment, AppointmentSlot, Reminder


def main() -> None:
    """Delete reminders, appointments, and slots while retaining doctors and departments."""
    init_db()
    db = SessionLocal()
    try:
        reminder_count = db.query(Reminder).delete()
        appointment_count = db.query(Appointment).delete()
        slot_count = db.query(AppointmentSlot).delete()
        db.commit()
        print(
            "Cleared "
            f"{reminder_count} reminders, {appointment_count} appointments, and {slot_count} slots."
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()