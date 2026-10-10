import os
import sys

# Add the parent directory to sys.path so we can import from the backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from database_models import AdminPasswordResetRequest

def run_migration():
    """
    Safely creates the new admin_password_reset_requests table without
    affecting existing tables or data.
    """
    print("Starting database migration for AdminPasswordResetRequest...")
    try:
        AdminPasswordResetRequest.__table__.create(bind=engine, checkfirst=True)
        print("Migration completed successfully. The table 'admin_password_reset_requests' is ready.")
    except Exception as e:
        print(f"Error during migration: {str(e)}")

if __name__ == "__main__":
    run_migration()
