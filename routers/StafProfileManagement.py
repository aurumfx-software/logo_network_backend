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


