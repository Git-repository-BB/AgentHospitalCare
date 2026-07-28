"""One-off: create/reset the admin account."""
from app.auth.security import hash_password
from app.database.db import SessionLocal, init_db
from app.database.models import User

USERNAME = "admin"
PASSWORD = "admin1234"

def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        print("Existing users:")
        for u in db.query(User).all():
            print(f"  {u.username} ({u.role})")

        user = db.query(User).filter(User.username == USERNAME).first()
        if user is None:
            user = User(username=USERNAME, hashed_password=hash_password(PASSWORD), role="administrator")
            db.add(user)
            db.commit()
            print(f"CREATED {USERNAME} / {PASSWORD} (administrator)")
        else:
            user.hashed_password = hash_password(PASSWORD)
            user.role = "administrator"
            db.commit()
            print(f"UPDATED {USERNAME} / {PASSWORD} (administrator)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
