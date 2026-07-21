"""Appointment scheduling: seeding demo doctors/slots, booking, and cancellation."""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from app.database.models import Appointment, AppointmentSlot, Department, Doctor


class NoSlotsAvailableError(Exception):
    """Raised when a department has no open appointment slots."""


def seed_doctors_and_slots(db: Session, slots_per_doctor: int = 5) -> None:
    """Idempotently ensure each clinical department has a doctor with upcoming open slots."""
    departments = db.query(Department).filter(Department.code != "front_desk").all()
    for department in departments:
        doctor = db.query(Doctor).filter(Doctor.department_id == department.id).first()
        if doctor is None:
            doctor = Doctor(name=f"Dr. {department.name} Specialist", department_id=department.id)
            db.add(doctor)
            db.commit()
            db.refresh(doctor)

        existing_open = (
            db.query(AppointmentSlot)
            .filter(AppointmentSlot.doctor_id == doctor.id, AppointmentSlot.is_booked.is_(False))
            .count()
        )
        if existing_open >= slots_per_doctor:
            continue

        start = dt.datetime.now(dt.timezone.utc).replace(minute=0, second=0, microsecond=0) + dt.timedelta(days=1)
        for i in range(slots_per_doctor - existing_open):
            slot_start = start + dt.timedelta(days=i, hours=9)
            db.add(
                AppointmentSlot(
                    doctor_id=doctor.id,
                    start_time=slot_start,
                    end_time=slot_start + dt.timedelta(minutes=30),
                    is_booked=False,
                )
            )
        db.commit()


def find_available_slots(db: Session, department_id: int, limit: int = 5) -> list[AppointmentSlot]:
    return (
        db.query(AppointmentSlot)
        .join(Doctor, AppointmentSlot.doctor_id == Doctor.id)
        .filter(Doctor.department_id == department_id, AppointmentSlot.is_booked.is_(False))
        .order_by(AppointmentSlot.start_time.asc())
        .limit(limit)
        .all()
    )


def book_appointment(db: Session, patient_id: str, department_id: int) -> Appointment:
    """Book the earliest available slot in a department for a patient."""
    slot = (
        db.query(AppointmentSlot)
        .join(Doctor, AppointmentSlot.doctor_id == Doctor.id)
        .filter(Doctor.department_id == department_id, AppointmentSlot.is_booked.is_(False))
        .order_by(AppointmentSlot.start_time.asc())
        .first()
    )
    if slot is None:
        raise NoSlotsAvailableError(f"No open slots for department {department_id}")

    slot.is_booked = True
    appointment = Appointment(
        patient_id=patient_id,
        department_id=department_id,
        doctor_id=slot.doctor_id,
        slot_id=slot.id,
        status="booked",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def cancel_appointment(db: Session, appointment_id: int) -> bool:
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if appointment is None:
        return False
    appointment.status = "cancelled"
    slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == appointment.slot_id).first()
    if slot is not None:
        slot.is_booked = False
    db.commit()
    return True
