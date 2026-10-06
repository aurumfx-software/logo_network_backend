from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database_models import Admin
from schemas.adminAuth import AdminProfileUpdateRequest
from utils.password import verify_password, hash_password
from utils.dependencies import get_current_admin

router = APIRouter(prefix="/admin-profile", tags=["Admin-profile"])

@router.put("/update")
def update_admin_profile(
    request: AdminProfileUpdateRequest, 
    db: Session = Depends(get_db), 
    admin: Admin = Depends(get_current_admin)
):
    if request.new_email != request.confirm_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email confirmation does not match"
        )
        
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password confirmation does not match"
        )
        
    if request.new_email != admin.email:
        existing_admin = db.query(Admin).filter(Admin.email == request.new_email).first()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered"
            )
            
    admin.email = request.new_email
    admin.password_hash = hash_password(request.new_password)
    db.commit()
    db.refresh(admin)
    
    return {
        "message": "Admin profile updated successfully",
        "admin": {
            "id": admin.id,
            "name": admin.name,
            "email": admin.email,
            "role": admin.role
        }
    }
