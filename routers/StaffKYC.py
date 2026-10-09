import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from database_models import Staff, KYCSubmission
from utils.dependencies import get_current_staff
from utils.spaces import upload_staff_image
from sqlalchemy import desc

router = APIRouter(prefix="/staff", tags=["Field Staff - KYC"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

@router.get("/kyc-status")
def get_kyc_status(db: Session = Depends(get_db), staff: Staff = Depends(get_current_staff)):
    latest_sub = db.query(KYCSubmission).filter(KYCSubmission.staff_id == staff.id).order_by(desc(KYCSubmission.submitted_at)).first()
    
    return {
        "staff_id": staff.staff_id,
        "kyc_status": staff.kyc_status,
        "aadhaar_front_image": staff.aadhaar_front_image,
        "aadhaar_back_image": staff.aadhaar_back_image,
        "latest_rejection_reason": latest_sub.rejection_reason if latest_sub and latest_sub.status == "REJECTED" else None,
        "latest_submitted_at": latest_sub.submitted_at if latest_sub else None,
        "latest_reviewed_at": latest_sub.reviewed_at if latest_sub else None
    }

@router.post("/kyc")
def upload_kyc(
    aadhaar_front_image: UploadFile = File(...),
    aadhaar_back_image: UploadFile = File(...),
    db: Session = Depends(get_db), 
    staff: Staff = Depends(get_current_staff)
):
    # Check if admin uploaded documents during registration
    first_kyc = db.query(KYCSubmission).filter(KYCSubmission.staff_id == staff.id).order_by(KYCSubmission.submitted_at.asc()).first()
    admin_supplied = False
    
    if first_kyc and staff.created_at and first_kyc.submitted_at:
        # If the first KYC submission was created within a few seconds of the staff record,
        # it means Admin uploaded it during the registration API call.
        diff = abs((first_kyc.submitted_at - staff.created_at).total_seconds())
        if diff < 10:
            admin_supplied = True
            
    if admin_supplied and staff.aadhaar_front_image and staff.aadhaar_back_image:
        raise HTTPException(
            status_code=400,
            detail="Your Aadhaar documents have already been uploaded by Admin. You cannot upload them again."
        )

    ext_front = os.path.splitext(aadhaar_front_image.filename)[1].lower()
    ext_back = os.path.splitext(aadhaar_back_image.filename)[1].lower()
    
    if ext_front not in ALLOWED_EXTENSIONS or ext_back not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Invalid image format")
        
    front_filename = f"{uuid.uuid4().hex}_front{ext_front}"
    back_filename = f"{uuid.uuid4().hex}_back{ext_back}"
    
    try:
        front_url = upload_staff_image(aadhaar_front_image.file, front_filename, aadhaar_front_image.content_type)
        back_url = upload_staff_image(aadhaar_back_image.file, back_filename, aadhaar_back_image.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    staff.aadhaar_front_image = front_url
    staff.aadhaar_back_image = back_url
    staff.kyc_status = "PENDING"
    
    new_kyc = KYCSubmission(
        staff_id=staff.id,
        aadhaar_front_image=front_url,
        aadhaar_back_image=back_url,
        status="PENDING"
    )
    
    db.add(new_kyc)
    db.commit()
    
    return {"message": "KYC documents submitted successfully", "kyc_status": "PENDING"}
