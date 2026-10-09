from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from database_models import Admin, KYCSubmission, Staff
from utils.dependencies import get_current_admin
from sqlalchemy import desc
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import List, Optional
import datetime

router = APIRouter(prefix="/admin/staff-kyc", tags=["Admin - Staff KYC"])

class RejectRequest(BaseModel):
    rejection_reason: str

@router.get("/pending")
def get_pending_kyc(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    submissions = db.query(KYCSubmission).filter(KYCSubmission.status == "PENDING").all()
    result = []
    for sub in submissions:
        result.append({
            "submission_id": sub.id,
            "staff_id": sub.staff.staff_id if sub.staff else None,
            "staff_name": sub.staff.name if sub.staff else None,
            "aadhaar_front_image": sub.aadhaar_front_image,
            "aadhaar_back_image": sub.aadhaar_back_image,
            "status": sub.status,
            "submitted_at": sub.submitted_at
        })
    return result

@router.patch("/{submission_id}/approve")
def approve_kyc(submission_id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    sub = db.query(KYCSubmission).filter(KYCSubmission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub.status != "PENDING":
        raise HTTPException(status_code=400, detail="Only pending submissions can be approved")
    
    sub.status = "APPROVED"
    sub.reviewer_id = admin.id
    sub.reviewed_at = func.now()
    
    if sub.staff:
        sub.staff.kyc_status = "APPROVED"
        
    db.commit()
    db.refresh(sub)
    
    return {
        "submission_id": sub.id,
        "staff_id": sub.staff.staff_id if sub.staff else None,
        "status": sub.status,
        "reviewed_at": sub.reviewed_at
    }

@router.patch("/{submission_id}/reject")
def reject_kyc(submission_id: int, request: RejectRequest, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    if not request.rejection_reason or not request.rejection_reason.strip():
        raise HTTPException(status_code=422, detail="Rejection reason is mandatory")
        
    sub = db.query(KYCSubmission).filter(KYCSubmission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub.status != "PENDING":
        raise HTTPException(status_code=400, detail="Only pending submissions can be rejected")
        
    sub.status = "REJECTED"
    sub.rejection_reason = request.rejection_reason
    sub.reviewer_id = admin.id
    sub.reviewed_at = func.now()
    
    if sub.staff:
        sub.staff.kyc_status = "REJECTED"
        
    db.commit()
    db.refresh(sub)
    
    return {
        "submission_id": sub.id,
        "status": sub.status,
        "rejection_reason": sub.rejection_reason,
        "reviewed_at": sub.reviewed_at
    }

@router.get("/approved")
def get_approved_kyc(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    submissions = db.query(KYCSubmission).filter(KYCSubmission.status == "APPROVED").all()
    result = []
    for sub in submissions:
        result.append({
            "submission_id": sub.id,
            "staff_id": sub.staff.staff_id if sub.staff else None,
            "staff_name": sub.staff.name if sub.staff else None,
            "aadhaar_front_image": sub.aadhaar_front_image,
            "aadhaar_back_image": sub.aadhaar_back_image,
            "status": sub.status,
            "submitted_at": sub.submitted_at,
            "reviewed_at": sub.reviewed_at,
            "reviewer_id": sub.reviewer_id
        })
    return result

@router.get("/rejected")
def get_rejected_kyc(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    submissions = db.query(KYCSubmission).filter(KYCSubmission.status == "REJECTED").all()
    result = []
    for sub in submissions:
        result.append({
            "submission_id": sub.id,
            "staff_id": sub.staff.staff_id if sub.staff else None,
            "staff_name": sub.staff.name if sub.staff else None,
            "aadhaar_front_image": sub.aadhaar_front_image,
            "aadhaar_back_image": sub.aadhaar_back_image,
            "status": sub.status,
            "rejection_reason": sub.rejection_reason,
            "submitted_at": sub.submitted_at,
            "reviewed_at": sub.reviewed_at,
            "reviewer_id": sub.reviewer_id
        })
    return result

@router.get("/history")
def get_kyc_history(staff_id: Optional[str] = None, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    query = db.query(KYCSubmission)
    if staff_id:
        staff = db.query(Staff).filter(Staff.staff_id == staff_id).first()
        if staff:
            query = query.filter(KYCSubmission.staff_id == staff.id)
        else:
            return []
            
    submissions = query.order_by(desc(KYCSubmission.submitted_at)).all()
    result = []
    for sub in submissions:
        result.append({
            "submission_id": sub.id,
            "staff_id": sub.staff.staff_id if sub.staff else None,
            "staff_name": sub.staff.name if sub.staff else None,
            "aadhaar_front_image": sub.aadhaar_front_image,
            "aadhaar_back_image": sub.aadhaar_back_image,
            "status": sub.status,
            "rejection_reason": sub.rejection_reason,
            "submitted_at": sub.submitted_at,
            "reviewed_at": sub.reviewed_at,
            "reviewer_id": sub.reviewer_id
        })
    return result
