# AgentCare Implementation Checkpoint

## Current status
- A basic FastAPI backend has been created.
- A Streamlit UI has been created.
- A simple workflow engine has been implemented.
- Safety escalation logic is included.
- A SQLite-based persistence layer has been added.
- Workflow runs are stored in a local database file.
- A basic agent-style orchestration structure has been introduced.
- Appointment and specialty routing has been improved so requests like “cardiologist” route to the correct department.
- Debug-friendly UI output has been added to display the request and workflow result.
- VS Code debug launch configurations for both the backend and the Streamlit UI have been added.

## Files created or modified
- [Agents.md](Agents.md)
- [requirements.txt](requirements.txt)
- [README.md](README.md)
- [app/__init__.py](app/__init__.py)
- [app/main.py](app/main.py)
- [app/workflow.py](app/workflow.py)
- [app/agents.py](app/agents.py)
- [app/database.py](app/database.py)
- [app/ui.py](app/ui.py)
- [app/__main__.py](app/__main__.py)
- [tests/test_workflow.py](tests/test_workflow.py)
- [tests/test_persistence.py](tests/test_persistence.py)

## Environment
- Virtual environment created at [.venv](.venv)
- Packages installed with uv

## Verified commands
- Tests run successfully with:
  - `.venv\Scripts\python.exe -m pytest -q`
- Result: 5 passed in 0.23s

## How to continue from here
1. Activate the virtual environment:
   - `.venv\Scripts\Activate.ps1`
2. Start the API in debug mode:
   - `.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
3. Start the UI in debug mode:
   - `.venv\Scripts\python.exe -m streamlit run app/ui.py --server.port 8501 --server.address 127.0.0.1`
4. Use the VS Code debug profiles named “Python: FastAPI Backend” and “Python: Streamlit UI” to step through the flow.
5. Review or extend the workflow in [app/workflow.py](app/workflow.py).
6. Add more advanced agent/tool behavior as needed.

## Notes
- The current implementation is a working prototype, not yet a full CrewAI-based production setup.
- The workflow is currently orchestrated manually through custom agent classes and SQLite persistence.
