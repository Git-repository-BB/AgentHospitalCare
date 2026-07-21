"""Run the CareFlow one agent at a time under the VS Code debugger.

How to use (like F10 in VS Code):
1. Put breakpoints in app/flows/stepwise_care_flow.py inside _run_step
   (e.g. on the coordinator / safety / routing blocks).
2. Run launch config: "Debug Workflow Steps (F10)"
3. Press F5 to start, then F10 / F11 to step through each agent.
4. When the terminal says "Press Enter", press Enter to run the next step.
"""
from __future__ import annotations

import pprint
import sys
from pathlib import Path

# Ensure project root is on sys.path when launched as a file or module.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.database.db import get_db, init_db
from app.flows.stepwise_care_flow import advance_session, start_session
from app.services import department_service


def main() -> None:
    init_db()
    db = get_db().__next__()
    try:
        department_service.seed_departments(db)
    finally:
        db.close()

    request_text = input(
        "Request text [default: I need to register as a new patient]: "
    ).strip() or "I need to register as a new patient"
    patient_id = input("Patient ID [default: P001]: ").strip() or "P001"

    session = start_session(request_text, patient_id)
    print("\nSession started:")
    pprint.pp(session)

    while not session["finished"]:
        input(f"\n>>> Press Enter to run next step: {session['next_step']}  ")
        # Breakpoint-friendly call: step into advance_session / _run_step with F11
        session = advance_session(session["session_id"])
        print(f"\nRan: {session['last_step']}")
        print(f"Detail: {session['last_step_detail']}")
        print(f"Next: {session['next_step']}")
        pprint.pp(session["result"])

    print("\nWorkflow finished.")
    pprint.pp(session)


if __name__ == "__main__":
    main()
