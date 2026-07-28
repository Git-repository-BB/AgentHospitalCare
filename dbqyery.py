from app.database.db import SessionLocal, init_db
from app.database.models import AuditLog, Department, Document, Escalation, Reminder, User ,PatientProfile ,Doctor   ,AppointmentSlot   ,Appointment, WorkflowRun          

db = SessionLocal()

users = db.query(PatientProfile).all()
AppointmentSlots = db.query(AppointmentSlot).all()

for AppointmentSlotss in AppointmentSlots:
    print(AppointmentSlotss.__dict__)

db.close()