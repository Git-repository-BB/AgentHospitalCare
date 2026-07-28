# AgentCare

AgentCare is an AI-powered healthcare administration workflow built with FastAPI, Streamlit, SQLAlchemy,
 and a real multi-agent [CrewAI](https://docs.crewai.com/) Flow backed by an LLM (OpenAI by default).

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
   - Copy `.env.example` to `.env` and set `OPENAI_API_KEY` (required for the agents to run) 

## Run locally

1. Start the API (creates/seeds the SQLite database on startup):
   - `uvicorn app.main:app --reload`
2. Start the UI:
   - `streamlit run streamlit/ui.py`
3. In the UI, register an account (creates a `patient`), for admin login use username as admin and password as admin. when logged in as admin it show the audit logs and esclations from the database.

## Architecture

```
app/
  agents/      CrewAI Agent factories (one per role, distinct prompts in app/prompts)
  api/         FastAPI routers (auth, admin)
  auth/        Password hashing + RBAC dependency
  database/    SQLAlchemy engine/session + ORM models
  flows/       CrewAI Flow orchestrating the agents end-to-end
  prompts/     Role/goal/backstory text per agent
  schemas/     Pydantic request/response and structured LLM output schemas
  services/    Business logic (departments, appointments, documents, reminders, escalation, audit)
  tools/       CrewAI tools wrapping services, callable by agents
streamlit/     Streamlit UI (talks to the API over HTTP with a JWT bearer token)
```

Agentic Orchestration


&#x20;               Streamlit UI



&#x20;                    │



&#x20;                FastAPI APIs



&#x20;                    │



&#x20;              CrewAI Flow



&#x20;                    │



&#x20;       Coordinator Agent (decide Intent)



&#x20;                    │


&#x20;            Safety Agent  ----->> Unsafe (asking medical advice) ---- esclation



&#x20;                    │   Safe

                       Routing

                          │

&#x20;  ┌──────────┬──────────┬─────────┬─────────┐



   Appointment Agent   Document Agent   Follow-up Agent



&#x20;                    │


&#x20;            Flow complete



The database used is SQLite database. It is in the repo.

## Usage


1. As new user first you have to register in the register tab and login with registered user id and password.
2. Now once you login to the AgentCare you can perform various activities as below.

Register the new patient.
Just type need to register patient. It will select random code PXXX Ex: P715 and return the patient id and the flow it has gone through. The details of the patient will be saved in the table PatientProfile. The patient name will not be considered for simplicity.

Book appointment
Fill the Patient ID tab and in request tab, just type required appointment with the specalist like cardilologist. It book the appointment and provide the appointment_id. That appointment details will be saved in the backend database table Appointment.

Cancel appointment
Fill the Patient ID tab and in request tab, Give you appointment id and ask to cancel in natural language it will cancel the apointment for that id and the cancellation entry will be in the Appointment table. Use dbqyery.py to query the database.

Document upload
Fill the Patient ID tab and in request tab enter need to upload document and select the file to be uplaoded. The details will be stored in the Document table.

other tables 
 AuditLog, Department, Document, Escalation, Reminder, User ,PatientProfile ,Doctor   ,AppointmentSlot   ,Appointment, WorkflowRun

Login as admin with user as admin and passwod as admin to see the esclated incidents.