import shutil
import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.admin_routes import router as admin_router
from app.api.auth_routes import router as auth_router
from app.auth.dependencies import require_role
from app.database.db import get_db, init_db
from app.flows.care_flow import run_care_flow
from app.flows.stepwise_care_flow import advance_session, get_session, start_session
from app.schemas.workflow import (
    PatientRequest,
    WorkflowNextRequest,
    WorkflowResponse,
    WorkflowStepResponse,
)
from app.services import department_service, workflow_service

app = FastAPI(title="AgentCare", version="0.3.0")
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


@app.post("/workflow", response_model=WorkflowResponse, tags=["workflow"])
def submit_workflow(
    payload: PatientRequest,
    _user=Depends(require_role("patient", "administrator")),
) -> WorkflowResponse:
    """Run the full multi-agent pipeline in one call."""
    try:
        result = run_care_flow(payload.request_text, payload.patient_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return WorkflowResponse(**result)


@app.post("/workflow/upload", response_model=WorkflowResponse, tags=["workflow"])
def submit_workflow_with_uploads(
    request_text: str = Form(...),
    patient_id: str | None = Form(default=None),
    files: list[UploadFile] = File(...),
    _user=Depends(require_role("patient", "administrator")),
) -> WorkflowResponse:
    """Run the existing workflow with one or more uploaded documents."""
    staging_dir = Path(tempfile.mkdtemp(prefix="agentcare-upload-"))
    document_paths: list[str] = []
    try:
        for index, uploaded_file in enumerate(files):
            filename = Path(uploaded_file.filename or f"upload-{index}").name
            destination = staging_dir / f"{index}_{filename}"
            with destination.open("wb") as output_file:
                shutil.copyfileobj(uploaded_file.file, output_file)
            document_paths.append(str(destination))

        result = run_care_flow(request_text, patient_id, document_paths)
        return WorkflowResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    finally:
        for uploaded_file in files:
            uploaded_file.file.close()
        shutil.rmtree(staging_dir, ignore_errors=True)


@app.post("/workflow/start", response_model=WorkflowStepResponse, tags=["workflow"])
def workflow_start(
    payload: PatientRequest,
    _user=Depends(require_role("patient", "administrator")),
) -> WorkflowStepResponse:
    """Start a stepwise session. Does not run any agent yet — call /workflow/next next."""
    data = start_session(payload.request_text, payload.patient_id)
    return WorkflowStepResponse(**data)


@app.post("/workflow/next", response_model=WorkflowStepResponse, tags=["workflow"])
def workflow_next(
    payload: WorkflowNextRequest,
    _user=Depends(require_role("patient", "administrator")),
) -> WorkflowStepResponse:
    """Run exactly one agent/pipeline step for an existing session."""
    try:
        data = advance_session(payload.session_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown session_id") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return WorkflowStepResponse(**data)


@app.get("/workflow/session/{session_id}", response_model=WorkflowStepResponse, tags=["workflow"])
def workflow_session(
    session_id: str,
    _user=Depends(require_role("patient", "administrator")),
) -> WorkflowStepResponse:
    """Inspect the current state of a stepwise session without advancing."""
    data = get_session(session_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown session_id")
    return WorkflowStepResponse(**data)


@app.get("/workflow-runs")
def workflow_runs(
    db: Session = Depends(get_db),
    _user=Depends(require_role("administrator")),
) -> list[dict[str, object]]:
    return workflow_service.list_workflow_runs(db)
