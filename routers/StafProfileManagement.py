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

@router.put("/profile")
def update_profile(
    update_data: StaffProfileUpdate,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    # Check password update first
    if update_data.current_password or update_data.new_password:
        if not update_data.current_password or not update_data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both current_password and new_password are required to change password"
            )
        
        if not verify_password(update_data.current_password, current_staff.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        current_staff.password_hash = hash_password(update_data.new_password)

    # Check email uniqueness
    if update_data.email and update_data.email != current_staff.email:
        if db.query(Staff).filter(Staff.email == update_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered by another staff member"
            )
        current_staff.email = update_data.email
        
    # Check phone uniqueness
    if update_data.phone and update_data.phone != current_staff.phone:
        if db.query(Staff).filter(Staff.phone == update_data.phone).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already registered by another staff member"
            )
        current_staff.phone = update_data.phone
        
    # Update other fields
    if update_data.name is not None:
        current_staff.name = update_data.name
    if update_data.address is not None:
        current_staff.address = update_data.address
        
    db.commit()
    db.refresh(current_staff)
    
    return {
        "message": "Profile updated successfully",
        "staff": StaffResponse.model_validate(current_staff)
    }
