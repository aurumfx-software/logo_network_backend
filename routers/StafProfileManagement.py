from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database_models import Staff
from schemas.staff import StaffProfileUpdate
from schemas.staffAuth import StaffResponse
from utils.dependencies import get_current_staff
from utils.password import verify_password, hash_password

router = APIRouter(prefix="/staff", tags=["FieldStaff - Profile"])

@router.get("/profile", response_model=StaffResponse)
def get_profile(current_staff: Staff = Depends(get_current_staff)):
    return current_staff

from schemas.staff import StaffAddressEmailUpdate

@router.put("/profile", response_model=StaffResponse)
def update_profile(
    update_data: StaffAddressEmailUpdate,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    if update_data.email is not None and update_data.email != current_staff.email:
        # Check if email is already taken
        existing_email = db.query(Staff).filter(Staff.email == update_data.email).first()
        if existing_email:
            raise HTTPException(status_code=409, detail="Email already registered")
        current_staff.email = update_data.email

    if update_data.address is not None:
        current_staff.address = update_data.address

    db.commit()
    db.refresh(current_staff)
    return current_staff
