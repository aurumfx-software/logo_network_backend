import os
import uuid
import secrets
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from database import get_db
from database_models import Admin, Staff, Business
from utils.dependencies import get_current_admin
from utils.spaces import upload_business_image, delete_business_image
from schemas.admin import StaffAdminResponse, StaffListResponse, StaffStatusUpdateRequest, StaffStatusUpdateResponse, BusinessListResponse, AdminStaffProfileUpdate
from schemas.business import BusinessResponse
from utils.password import hash_password
from schemas.staffAuth import StaffRegisterRequest, StaffResponse

router = APIRouter(prefix="/admin")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.get("/staff", response_model=StaffListResponse, tags=["Admin Staff Management"])
def admin_get_staff(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    staff_list = db.query(Staff).all()
    businesses = db.query(Business).all()
    
    business_map = {}
    for b in businesses:
        if b.staff_id:
            if b.staff_id not in business_map:
                business_map[b.staff_id] = []
            business_map[b.staff_id].append(b)
            
    result = []
    for staff in staff_list:
        staff_businesses = business_map.get(staff.staff_id, [])
        result.append({
            "id": staff.id,
            "staff_id": staff.staff_id,
            "name": staff.name,
            "email": staff.email,
            "phone": staff.phone,
            "address": staff.address,
            "role": staff.role,
            "status": staff.status,
            "created_at": staff.created_at,
            "businesses": staff_businesses,
            "total_businesses": len(staff_businesses)
        })
        
    return {"staff": result, "total": len(result)}

def generate_staff_id(db: Session) -> str:
    while True:
        rand_digits = f"{secrets.randbelow(1000):03d}"
        new_id = f"SF{rand_digits}"
        if not db.query(Staff).filter(Staff.staff_id == new_id).first():
            return new_id

@router.post("/staff/register", tags=["Admin Staff Management"])
def admin_register_staff(request: StaffRegisterRequest, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    if db.query(Staff).filter(Staff.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(Staff).filter(Staff.phone == request.phone).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    from sqlalchemy.exc import IntegrityError
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
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
                "message": "Field Staff created successfully",
                "staff_id": new_staff.staff_id,
                "user_id": new_staff.id,
                "name": new_staff.name,
                "email": new_staff.email
            }
        except IntegrityError:
            db.rollback()
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail="Failed to generate a unique staff ID. Please try again.")

@router.get("/staff/search/{staff_id}", response_model=StaffAdminResponse, tags=["Admin Staff Management"])
def admin_search_staff_by_id(staff_id: str, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    staff = db.query(Staff).filter(Staff.staff_id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
        
    businesses = db.query(Business).filter(Business.staff_id == staff.staff_id).all()
    
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
        "businesses": businesses,
        "total_businesses": len(businesses)
    }

@router.get("/staff/{id}", response_model=StaffAdminResponse, tags=["Admin Staff Management"])
def admin_get_one_staff(id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    staff = db.query(Staff).filter(Staff.id == id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
        
    businesses = db.query(Business).filter(Business.staff_id == staff.staff_id).all()
    
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
        "businesses": businesses,
        "total_businesses": len(businesses)
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


