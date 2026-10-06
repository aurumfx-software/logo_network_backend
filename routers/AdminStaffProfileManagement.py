from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database_models import Admin, Staff
from utils.dependencies import get_current_admin
from utils.password import hash_password
from schemas.staffAuth import StaffResponse
from schemas.admin import AdminStaffProfileUpdate

router = APIRouter(prefix="/admin", tags=["Admin Staff Profile Management"])

@router.get("/staff/{id}/profile", response_model=StaffResponse)
def admin_get_staff_profile(id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    staff = db.query(Staff).filter(Staff.id == id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
        
    return staff

@router.put("/staff/{id}/profile", response_model=StaffResponse)
def admin_update_staff_profile(id: int, update_data: AdminStaffProfileUpdate, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    staff = db.query(Staff).filter(Staff.id == id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
        
    if update_data.email and update_data.email != staff.email:
        if db.query(Staff).filter(Staff.email == update_data.email).first():
            raise HTTPException(status_code=409, detail="Email already registered")
        staff.email = update_data.email
        
    if update_data.phone and update_data.phone != staff.phone:
        if db.query(Staff).filter(Staff.phone == update_data.phone).first():
            raise HTTPException(status_code=409, detail="Phone already registered")
        staff.phone = update_data.phone
        
    if update_data.name is not None:
        staff.name = update_data.name
        
    if update_data.address is not None:
        staff.address = update_data.address
        
    if update_data.password is not None and update_data.password != "":
        staff.password_hash = hash_password(update_data.password)
        
    db.commit()
    db.refresh(staff)
    return staff
