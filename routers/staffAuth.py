import random
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database_models import Staff
from schemas.staffAuth import StaffRegisterRequest, StaffLoginRequest, StaffResponse
from utils.password import hash_password, verify_password
from utils.jwt import create_access_token

router = APIRouter(prefix="/staff-auth", tags=["FieldStaff - Authentication"])


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
