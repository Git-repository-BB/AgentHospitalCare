"""Patient profile lookups. Business logic only; no direct API concerns here."""
from __future__ import annotations

import random

from sqlalchemy.orm import Session

from app.database.models import PatientProfile


def generate_patient_id(db: Session) -> str:
    """Generate an unused patient identifier in the PXXX format."""
    while True:
        patient_id = f"P{random.randint(0, 999):03d}"
        exists = db.query(PatientProfile.id).filter(PatientProfile.patient_id == patient_id).first()
        if exists is None:
            return patient_id


def get_or_create_patient(db: Session, patient_id: str) -> PatientProfile:
    """Return the patient profile for patient_id, creating a bare-bones one if needed."""
    profile = db.query(PatientProfile).filter(PatientProfile.patient_id == patient_id).first()
    if profile is None:
        profile = PatientProfile(patient_id=patient_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile
