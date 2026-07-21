from app.services import audit_service, escalation_service


def test_create_and_resolve_escalation(db_session) -> None:
    escalation = escalation_service.create_escalation(db_session, "patient-1", "diagnose my chest pain", "requested diagnosis")

    unresolved = escalation_service.list_escalations(db_session, resolved=False)
    assert len(unresolved) == 1

    escalation_service.resolve_escalation(db_session, escalation.id)
    assert escalation_service.list_escalations(db_session, resolved=False) == []
    assert len(escalation_service.list_escalations(db_session, resolved=True)) == 1


def test_audit_log_action_is_recorded(db_session) -> None:
    audit_service.log_action(db_session, actor="safety_agent", action="safety_escalation", details="unsafe request")

    logs = audit_service.list_audit_logs(db_session)
    assert len(logs) == 1
    assert logs[0].actor == "safety_agent"
    assert logs[0].action == "safety_escalation"
