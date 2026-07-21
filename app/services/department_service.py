"""Department directory and specialty routing logic."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.models import Department

DEFAULT_DEPARTMENTS: list[tuple[str, str]] = [
    ("front_desk", "Front Desk"),
    ("appointments", "Appointments"),
    ("cardiology", "Cardiology"),
    ("neurology", "Neurology"),
    ("dermatology", "Dermatology"),
    ("pediatrics", "Pediatrics"),
    ("orthopedics", "Orthopedics"),
]

SPECIALTY_KEYWORDS: dict[str, str] = {
    "cardiology": "cardiology",
    "cardiologist": "cardiology",
    "heart": "cardiology",
    "neurology": "neurology",
    "neurologist": "neurology",
    "brain": "neurology",
    "dermatology": "dermatology",
    "dermatologist": "dermatology",
    "skin": "dermatology",
    "pediatrics": "pediatrics",
    "pediatrician": "pediatrics",
    "paediatrics": "pediatrics",
    "child": "pediatrics",
    "orthopedics": "orthopedics",
    "orthopedic": "orthopedics",
    "bone": "orthopedics",
    "joint": "orthopedics",
}


def seed_departments(db: Session) -> None:
    """Idempotently ensure the default department list exists."""
    existing_codes = {code for (code,) in db.query(Department.code).all()}
    for code, name in DEFAULT_DEPARTMENTS:
        if code not in existing_codes:
            db.add(Department(code=code, name=name))
    db.commit()


def lookup_department(db: Session, text: str) -> Department:
    """Match specialty keywords in free text, falling back to the front desk."""
    normalized = text.lower()
    matched_code = "front_desk"
    for keyword, code in SPECIALTY_KEYWORDS.items():
        if keyword in normalized:
            matched_code = code
            break
    else:
        if "appointment" in normalized or "book" in normalized:
            matched_code = "appointments"

    department = db.query(Department).filter(Department.code == matched_code).first()
    if department is None:
        department = db.query(Department).filter(Department.code == "front_desk").first()
    return department


def get_department_by_code(db: Session, code: str) -> Department | None:
    return db.query(Department).filter(Department.code == code).first()
