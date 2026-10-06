from sqlalchemy import text
from database import SessionLocal
from database_models import Business, Staff

db = SessionLocal()

# Drop foreign key constraint
db.execute(text("ALTER TABLE businesses DROP CONSTRAINT IF EXISTS businesses_staff_id_fkey;"))
# Alter the column type
db.execute(text("ALTER TABLE businesses ALTER COLUMN staff_id TYPE VARCHAR;"))
db.commit()

businesses = db.query(Business).all()
for business in businesses:
    if business.staff_id and str(business.staff_id).isdigit():
        staff = db.query(Staff).filter(Staff.id == int(business.staff_id)).first()
        if staff:
            business.staff_id = staff.staff_id
            print(f"Updated Business {business.id} staff_id to {staff.staff_id}")

db.commit()
db.close()
print("Migration completed.")
