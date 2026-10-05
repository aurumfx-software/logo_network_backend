import os
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from database import get_db
from database_models import Admin, Staff, Business
from utils.dependencies import get_current_admin
from utils.spaces import upload_business_image, delete_business_image
from schemas.admin import StaffAdminResponse, StaffListResponse, StaffStatusUpdateRequest, StaffStatusUpdateResponse, BusinessListResponse
from schemas.business import BusinessResponse

router = APIRouter(prefix="/admin")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.get("/staff", response_model=StaffListResponse, tags=["Admin Staff Management"])
def admin_get_staff(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    staff_list = db.query(Staff).all()
    return {"staff": staff_list, "total": len(staff_list)}

@router.get("/staff/{id}", response_model=StaffAdminResponse, tags=["Admin Staff Management"])
def admin_get_one_staff(id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    staff = db.query(Staff).filter(Staff.id == id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
        
    businesses = db.query(Business).filter(Business.staff_id == staff.id).all()
    
    return {
        "id": staff.id,
        "staff_id": staff.staff_id,
        "name": staff.name,
        "email": staff.email,
        "phone": staff.phone,
        "address": staff.address,
        "role": staff.role,
        "status": staff.status,
        "created_at": staff.created_at,
        "businesses": businesses
    }

@router.patch("/staff/{id}/status", response_model=StaffStatusUpdateResponse, tags=["Admin Staff Management"])
def admin_update_staff_status(id: int, request: StaffStatusUpdateRequest, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    if request.status not in ["Active", "Deactivate"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be 'Active' or 'Deactivate'")
    
    staff = db.query(Staff).filter(Staff.id == id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    staff.status = request.status
    db.commit()
    db.refresh(staff)
    
    return {
        "message": f"Staff {'activated' if request.status == 'Active' else 'deactivated'} successfully",
        "staff": staff
    }


