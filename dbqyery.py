from app.database.db import SessionLocal, init_db
from app.database.models import AuditLog, Department, Document, Escalation, Reminder, User ,PatientProfile ,Doctor   ,AppointmentSlot   ,Appointment, WorkflowRun          

db = SessionLocal()

users = db.query(Appointment).all()
Appointmen = db.query(Appointment).all()

for AppointmentSlotss in Appointmen:
    print(AppointmentSlotss.__dict__)

db.close()