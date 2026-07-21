from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.api.admin_routes import router as admin_router
from app.api.auth_routes import router as auth_router
from app.auth.dependencies import require_role
from app.database.db import get_db, init_db
from app.flows.care_flow import run_care_flow
from app.schemas.workflow import PatientRequest, WorkflowResponse
from app.services import department_service, workflow_service

app = FastAPI(title="AgentCare", version="0.2.0")
app.include_router(auth_router)
app.include_router(admin_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    db = get_db().__next__()
    try:
        department_service.seed_departments(db)
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/workflow", response_model=WorkflowResponse)
def submit_workflow(
    payload: PatientRequest,
    _user=Depends(require_role("patient", "administrator")),
) -> WorkflowResponse:
    try:
        result = run_care_flow(payload.request_text, payload.patient_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return WorkflowResponse(**result)


@app.get("/workflow-runs")
def workflow_runs(
    db: Session = Depends(get_db),
    _user=Depends(require_role("administrator")),
) -> list[dict[str, object]]:
    return workflow_service.list_workflow_runs(db)
