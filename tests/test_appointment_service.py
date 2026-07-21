import pytest

from app.services import appointment_service, department_service


def test_book_appointment_picks_earliest_slot(db_session) -> None:
    department_service.seed_departments(db_session)
    appointment_service.seed_doctors_and_slots(db_session)
    department = department_service.get_department_by_code(db_session, "cardiology")

    appointment = appointment_service.book_appointment(db_session, "patient-1", department.id)

    assert appointment.patient_id == "patient-1"
    assert appointment.department_id == department.id
    assert appointment.status == "booked"


def test_book_appointment_raises_when_no_slots_left(db_session) -> None:
    department_service.seed_departments(db_session)
    appointment_service.seed_doctors_and_slots(db_session, slots_per_doctor=1)
    department = department_service.get_department_by_code(db_session, "neurology")

    appointment_service.book_appointment(db_session, "patient-1", department.id)

    with pytest.raises(appointment_service.NoSlotsAvailableError):
        appointment_service.book_appointment(db_session, "patient-2", department.id)


def test_cancel_appointment_frees_the_slot(db_session) -> None:
    department_service.seed_departments(db_session)
    appointment_service.seed_doctors_and_slots(db_session)
    department = department_service.get_department_by_code(db_session, "dermatology")
    appointment = appointment_service.book_appointment(db_session, "patient-1", department.id)

    assert appointment_service.cancel_appointment(db_session, appointment.id) is True
    assert appointment_service.cancel_appointment(db_session, 999999) is False
