from app.services import department_service


def test_seed_departments_is_idempotent(db_session) -> None:
    department_service.seed_departments(db_session)
    department_service.seed_departments(db_session)

    codes = {d.code for d in db_session.query(department_service.Department).all()}
    assert codes == {code for code, _ in department_service.DEFAULT_DEPARTMENTS}


def test_lookup_department_matches_specialty_keywords(db_session) -> None:
    department_service.seed_departments(db_session)

    assert department_service.lookup_department(db_session, "I need a cardiologist").code == "cardiology"
    assert department_service.lookup_department(db_session, "my child needs a checkup").code == "pediatrics"
    assert department_service.lookup_department(db_session, "book an appointment please").code == "appointments"
    assert department_service.lookup_department(db_session, "general question").code == "front_desk"
