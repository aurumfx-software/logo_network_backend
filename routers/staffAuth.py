import random
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database_models import Staff
from schemas.staffAuth import StaffRegisterRequest, StaffLoginRequest, StaffResponse
from utils.password import hash_password, verify_password
from utils.jwt import create_access_token

router = APIRouter(prefix="/staff-auth", tags=["FieldStaff - Authentication"])

def generate_staff_id(db: Session) -> str:
    while True:
        random_num = random.randint(100, 99999)
        new_id = f"STAFF-{random_num}"
        if not db.query(Staff).filter(Staff.staff_id == new_id).first():
            return new_id


# staff registration API
@router.post("/register")
def register_staff(request: StaffRegisterRequest, db: Session = Depends(get_db)):
    if db.query(Staff).filter(Staff.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(Staff).filter(Staff.phone == request.phone).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    staff_id = generate_staff_id(db)
    
    new_staff = Staff(
        staff_id=staff_id,
        name=request.name,
        email=request.email,
        password_hash=hash_password(request.password),
        phone=request.phone,
        address=request.address
    )
    
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    
    return {
        "message": "Staff registered successfully",
        "staff": StaffResponse.model_validate(new_staff)
    }


# staff login API
@router.post("/login")
def login_staff(request: StaffLoginRequest, db: Session = Depends(get_db)):
    staff = db.query(Staff).filter(Staff.staff_id == request.staff_id).first()
    if not staff:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if not verify_password(request.password, staff.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if not staff.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")
        
    if staff.status == "Deactivate":
        raise HTTPException(status_code=403, detail="Staff account is deactivated")
        
    access_token = create_access_token(data={"sub": staff.staff_id, "id": staff.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "staff": StaffResponse.model_validate(staff)
    }
