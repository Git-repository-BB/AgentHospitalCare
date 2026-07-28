import random

from app.database.models import PatientProfile
from app.services import patient_service


def test_generate_patient_id_uses_unused_pxxx_value(db_session, monkeypatch) -> None:
    db_session.add(PatientProfile(patient_id="P123"))
    db_session.commit()
    values = iter([123, 456])
    monkeypatch.setattr(random, "randint", lambda _start, _end: next(values))

    patient_id = patient_service.generate_patient_id(db_session)

    assert patient_id == "P456"