from app.database.db import SessionLocal, init_db
from app.database.models import AuditLog, Department, Document, Escalation, Reminder, User ,PatientProfile ,Doctor   ,AppointmentSlot   ,Appointment, WorkflowRun          

db = SessionLocal()

users = db.query(PatientProfile).all()
Appointments = db.query(Appointment).all()

for Appointmen in Appointments:
    print(Appointmen.__dict__)



db.close()


#try:
#    deleted = db.query(Escalation).delete()
#    db.commit()
#    print(f"Deleted {deleted} rows.")
#finally:
#    db.close()