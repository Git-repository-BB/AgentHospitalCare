"""Tools the Appointment Agent uses to check availability and book/cancel appointments."""
from __future__ import annotations

from crewai.tools import tool

from app.database.db import SessionLocal
from app.services import appointment_service, department_service


@tool("Appointment Availability Tool")
def appointment_availability_tool(department_code: str) -> str:
    """List upcoming open appointment slots for a department code.

    Args:
        department_code: The department code, e.g. "cardiology".

    Returns:
        A semicolon-separated list of "slot_id|start_time" entries, or a
        message stating no slots are available.
    """
    db = SessionLocal()
    try:
        department_service.seed_departments(db)
        department = department_service.get_department_by_code(db, department_code)
        if department is None:
            return f"Unknown department code: {department_code}"
        appointment_service.seed_doctors_and_slots(db)
        slots = appointment_service.find_available_slots(db, department.id)
        if not slots:
            return f"No open slots currently available for {department_code}."
        return ";".join(f"{slot.id}|{slot.start_time.isoformat()}" for slot in slots)
    finally:
        db.close()


@tool("Appointment Booking Tool")
def appointment_booking_tool(patient_id: str, department_code: str) -> str:
    """Book the earliest available appointment slot for a patient in a department.

    Args:
        patient_id: Identifier of the patient booking the appointment.
        department_code: The department code, e.g. "cardiology".

    Returns:
        A string "appointment_id|start_time" on success, or an error message.
    """
    db = SessionLocal()
    try:
        department_service.seed_departments(db)
        department = department_service.get_department_by_code(db, department_code)
        if department is None:
            return f"Unknown department code: {department_code}"
        appointment_service.seed_doctors_and_slots(db)
        try:
            appointment = appointment_service.book_appointment(db, patient_id, department.id)
        except appointment_service.NoSlotsAvailableError:
            return f"No open slots currently available for {department_code}."
        slot = appointment.slot_id
        return f"{appointment.id}|{appointment.created_at.isoformat()}|slot:{slot}"
    finally:
        db.close()


@tool("Appointment Cancellation Tool")
def appointment_cancellation_tool(appointment_id: str) -> str:
    """Cancel a previously booked appointment by its id.

    Args:
        appointment_id: The numeric id of the appointment to cancel.

    Returns:
        A confirmation or failure message.
    """
    db = SessionLocal()
    try:
        ok = appointment_service.cancel_appointment(db, int(appointment_id))
        return "cancelled" if ok else f"Appointment {appointment_id} not found."
    finally:
        db.close()
