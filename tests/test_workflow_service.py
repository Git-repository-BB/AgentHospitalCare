from app.services import workflow_service


def test_workflow_run_round_trip(db_session) -> None:
    workflow_service.save_workflow_run(
        db_session,
        {
            "patient_id": "p1",
            "department_id": "cardiology",
            "appointment_id": "1",
            "workflow_status": "COMPLETED",
            "escalated": False,
            "intent": "cardiology",
            "agent_plan": ["coordinator", "routing", "appointment"],
            "summary": "Routed to cardiology",
            "steps": ["patient_registration", "appointment_booking"],
        }
    )

    runs = workflow_service.list_workflow_runs(db_session)

    assert len(runs) == 1
    assert runs[0]["workflow_status"] == "COMPLETED"
    assert runs[0]["agent_plan"] == ["coordinator", "routing", "appointment"]
    assert runs[0]["steps"] == ["patient_registration", "appointment_booking"]
