import sys
from sqlalchemy.orm import Session
from database import SessionLocal
from database_models import Admin
from utils.password import hash_password

def seed_admin():
    db: Session = SessionLocal()
    try:
        print("--- Create Admin ---")
        name = input("Enter admin name: ").strip()
        email = input("Enter admin email: ").strip()
        password = input("Enter admin password: ").strip()

        if not name or not email or not password:
            print("Name, email, and password are required.")
            return

        existing_admin = db.query(Admin).filter(Admin.email == email).first()
        if existing_admin:
            print(f"Admin with email {email} already exists.")
            return

        hashed_password = hash_password(password)
        
        new_admin = Admin(
            name=name,
            email=email,
            password_hash=hashed_password,
            role="admin",
            is_active=True
        )
        
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        
        print(f"Success! Admin created with ID: {new_admin.id}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
