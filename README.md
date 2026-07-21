# AgentCare

AgentCare is an AI-powered healthcare administration workflow built with FastAPI, Streamlit, SQLAlchemy,
JWT auth, and a real multi-agent [CrewAI](https://docs.crewai.com/) Flow backed by an LLM (OpenAI by default).

Agents (Coordinator, Safety, Routing, Appointment, Document, Follow-up) reason over each patient request
with the LLM and call tools backed by real services (department directory, appointment booking, document
storage/duplicate detection, reminders/notifications, safety escalation, audit logging) — see [Agents.md](Agents.md)
for the full design.

## Setup

1. Create and activate a virtual environment:
   - PowerShell: `python -m venv .venv; .venv\Scripts\Activate.ps1`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Configure environment variables:
   - Copy `.env.example` to `.env` and set `OPENAI_API_KEY` (required for the agents to run) and
     `AGENTCARE_JWT_SECRET` (recommended for anything beyond local dev).

## Run locally

1. Start the API (creates/seeds the SQLite database on startup):
   - `uvicorn app.main:app --reload`
2. Start the UI:
   - `streamlit run streamlit/ui.py`
3. In the UI, register an account (creates a `patient`), or call `POST /auth/bootstrap-admin`
   once to create the first `administrator` account (only works while no users exist yet).

## Architecture

```
app/
  agents/      CrewAI Agent factories (one per role, distinct prompts in app/prompts)
  api/         FastAPI routers (auth, admin)
  auth/        Password hashing + JWT issuing/verification, RBAC dependency
  database/    SQLAlchemy engine/session + ORM models
  flows/       CrewAI Flow orchestrating the agents end-to-end
  prompts/     Role/goal/backstory text per agent
  schemas/     Pydantic request/response and structured LLM output schemas
  services/    Business logic (departments, appointments, documents, reminders, escalation, audit)
  tools/       CrewAI tools wrapping services, callable by agents
streamlit/     Streamlit UI (talks to the API over HTTP with a JWT bearer token)
```

## Tests

- `pytest -q`

Tests for services/tools/database logic run without any LLM calls. Tests that exercise the full
CrewAI Flow require `OPENAI_API_KEY` to be set and are skipped automatically otherwise.
