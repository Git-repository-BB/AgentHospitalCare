\# AGENTS.md



\# AgentCare - Agentic AI for Patient Administration and Care Coordination



\## Project Overview



AgentCare is an AI-powered healthcare administration platform that automates \*\*non-clinical patient workflows\*\* using CrewAI.



The system \*\*does NOT diagnose diseases or prescribe treatments\*\*.



Its responsibilities include:



\- Patient Registration

\- Administrative Intent Detection

\- Department Routing

\- Appointment Booking

\- Document Management

\- Reminder Scheduling

\- Workflow Tracking

\- Human Escalation

\- Audit Logging



The application follows an Agentic AI architecture where multiple specialized agents collaborate to complete administrative workflows.



\---



\# Technology Stack



Backend:

\- Python

\- FastAPI

\- CrewAI

\- SQLAlchemy

\- PostgreSQL (SQLite during development)



Frontend:

\- Streamlit



LLM:

\- OpenAI GPT

\- Gemini (optional)



Document Processing:

\- PyMuPDF

\- Unstructured

\- OCR (optional)



Authentication:

\- JWT



Scheduling:

\- APScheduler



\---



\# Architecture



```

&#x20;               Streamlit UI



&#x20;                    │



&#x20;                FastAPI APIs



&#x20;                    │



&#x20;             Authentication



&#x20;                    │



&#x20;              CrewAI Flow



&#x20;                    │



&#x20;       Coordinator Agent



&#x20;                    │



&#x20;  ┌──────────┬──────────┬─────────┬─────────┐



Routing   Appointment  Document  Follow-up



&#x20;                    │



&#x20;            Safety Agent



&#x20;                    │



&#x20;            Human Escalation



&#x20;                    │



&#x20;             PostgreSQL Database

```



\---



\# Design Principles



Every agent should have:



\- One responsibility

\- Independent prompt

\- Independent tools

\- No business logic duplication

\- No SQL queries inside agent prompts



Business logic belongs inside Tools.



Database access belongs inside Services.



Agents only reason and decide.



\---



\# Workflow



Patient Request



↓



Coordinator Agent



↓



Routing Agent



↓



Appointment Agent



↓



Document Agent



↓



Reminder Agent



↓



Workflow Completed



OR



↓



Safety Agent



↓



Human Escalation



\---



\# Agents



\## 1 Coordinator Agent



\### Responsibility



Acts as the orchestrator.



Understands the patient request.



Determines the workflow.



Delegates work.



Never directly modifies the database.



\### Input



Natural language request.



\### Output



Workflow plan.



Example



```

Need registration



Need appointment



Need reminder

```



Tools



None



\---



\## 2 Routing Agent



\### Responsibility



Determine which department should receive the request.



Examples



Cardiology



Neurology



Dermatology



Pediatrics



Orthopedics



\### Tools



DepartmentLookupTool



\### Output



Department ID



\---



\## 3 Appointment Agent



\### Responsibility



Manage appointments.



Capabilities



\- Find available doctors

\- Check slots

\- Book appointment

\- Reschedule appointment

\- Cancel appointment



\### Tools



AppointmentAvailabilityTool



AppointmentBookingTool



AppointmentCancellationTool



\---



\## 4 Document Agent



\### Responsibility



Process uploaded files.



Capabilities



\- Store files

\- Extract metadata

\- Identify document type

\- Detect duplicates

\- Detect missing required documents



\### Tools



DocumentParserTool



DocumentStorageTool



DuplicateDetectionTool



\---



\## 5 Follow-up Agent



\### Responsibility



Schedule reminders.



Generate follow-up tasks.



Notify patient.



\### Tools



ReminderTool



NotificationTool



\---



\## 6 Safety Agent



\### Responsibility



Protect against unsafe behavior.



Must detect



\- Diagnosis requests

\- Prescription requests

\- Medical advice

\- Emergency situations



Creates escalation records.



Never answers medical questions.



\### Tools



EscalationTool



AuditTool



\---



\# Flow State



The CrewAI Flow maintains shared state.



Example



```python

{

&#x20;   "patient\_id": None,

&#x20;   "department\_id": None,

&#x20;   "appointment\_id": None,

&#x20;   "documents": \[],

&#x20;   "workflow\_status": "RUNNING",

&#x20;   "escalated": False

}

```



Each agent updates only its own fields.



\---



\# Database



Core Tables



Users



PatientProfiles



Departments



Doctors



AppointmentSlots



Appointments



Documents



WorkflowRuns



Reminders



Escalations



AuditLogs



\---



\# Folder Structure



```

app/



&#x20;   agents/



&#x20;   crews/



&#x20;   flows/



&#x20;   tools/



&#x20;   services/



&#x20;   database/



&#x20;   api/



&#x20;   models/



&#x20;   schemas/



&#x20;   prompts/



streamlit/



tests/



uploads/

```



\---



\# Coding Standards



Always



\- Use type hints



\- Use Pydantic schemas



\- Use dependency injection



\- Use SQLAlchemy ORM



\- Write docstrings



\- Log important actions



Never



\- Hardcode responses



\- Embed SQL inside agents



\- Access database directly from agents



\- Put secrets in code



\---



\# Error Handling



Every tool must



\- Catch exceptions



\- Log failures



\- Return structured errors



Agents should never crash the workflow.



Coordinator decides retries.



\---



\# Logging



Log



\- Agent execution



\- Tool execution



\- Database updates



\- Escalations



\- User actions



\- Errors



\---



\# Security



Authentication via JWT.



Backend enforces RBAC.



Roles



Patient



Administrator



Only administrators can



\- Approve escalations



\- Manage doctors



\- Manage departments



\- View audit logs



\---



\# Safety Rules



The AI must NEVER



\- Diagnose disease



\- Recommend medicines



\- Recommend dosage



\- Interpret lab reports clinically



\- Replace a physician



If detected



↓



Invoke Safety Agent



↓



Create Escalation



↓



Notify Administrator



\---



\# Prompt Engineering



Every agent must have



Role



Goal



Backstory



Tools



Expected Output



No two agents should share identical prompts.



\---



\# Testing



Unit Tests



\- Tool logic



\- Services



Integration Tests



\- Crew workflow



\- Database persistence



End-to-End



Patient request



↓



Appointment booked



↓



Reminder created



↓



Audit log generated



\---





\---



\# Success Criteria



A successful request should



✓ Identify patient



✓ Determine intent



✓ Route department



✓ Book appointment



✓ Store documents



✓ Schedule reminder



✓ Persist workflow



✓ Log audit trail



✓ Escalate unsafe requests



without human intervention unless escalation is required.

