from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from database_models import Admin, Staff
from utils.dependencies import get_current_admin
from utils.password import hash_password
from schemas.staffAuth import StaffResponse
from typing import Optional
from utils.spaces import upload_staff_image
import os
import uuid

router = APIRouter(prefix="/admin", tags=["Admin Staff Profile Management"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

@router.get("/staff/{id}/profile", response_model=StaffResponse)
def admin_get_staff_profile(id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    staff = db.query(Staff).filter(Staff.id == id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
        
    return staff

@router.put("/staff/{id}/profile", response_model=StaffResponse)
def admin_update_staff_profile(
    id: int, 
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    aadhaar_number: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    district: Optional[str] = Form(None),
    aadhaar_front_image: Optional[UploadFile] = File(None),
    aadhaar_back_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db), 
    admin: Admin = Depends(get_current_admin)
):
    staff = db.query(Staff).filter(Staff.id == id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
        
    if email and email != staff.email:
        if db.query(Staff).filter(Staff.email == email).first():
            raise HTTPException(status_code=409, detail="Email already registered")
        staff.email = email
        
    if phone and phone != staff.phone:
        if db.query(Staff).filter(Staff.phone == phone).first():
            raise HTTPException(status_code=409, detail="Phone already registered")
        staff.phone = phone
        
    if name is not None:
        staff.name = name
        
    if address is not None:
        staff.address = address
        
    if state is not None:
        staff.state = state
        
    if district is not None:
        staff.district = district
        
    if aadhaar_number is not None:
        normalized_aadhaar = aadhaar_number.replace(" ", "").replace("-", "")
        if not normalized_aadhaar.isdigit() or len(normalized_aadhaar) != 12:
            raise HTTPException(status_code=422, detail="Aadhaar number must be exactly 12 digits")
        staff.aadhaar_number = normalized_aadhaar
        
    if password is not None and password != "":
        staff.password_hash = hash_password(password)

    if aadhaar_front_image and aadhaar_front_image.filename:
        ext = os.path.splitext(aadhaar_front_image.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=422, detail="Invalid front image format")
        filename = f"{uuid.uuid4().hex}_front{ext}"
        staff.aadhaar_front_image = upload_staff_image(aadhaar_front_image.file, filename, aadhaar_front_image.content_type)

    if aadhaar_back_image and aadhaar_back_image.filename:
        ext = os.path.splitext(aadhaar_back_image.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=422, detail="Invalid back image format")
        filename = f"{uuid.uuid4().hex}_back{ext}"
        staff.aadhaar_back_image = upload_staff_image(aadhaar_back_image.file, filename, aadhaar_back_image.content_type)
        
    db.commit()
    db.refresh(staff)
    return staff
