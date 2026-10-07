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
    if not any([request.new_email, request.confirm_email, request.new_password, request.confirm_password]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update."
        )

    if request.new_email or request.confirm_email:
        if not (request.new_email and request.confirm_email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both new_email and confirm_email must be provided"
            )
        if request.new_email != request.confirm_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email confirmation does not match"
            )
        if request.new_email != admin.email:
            existing_admin = db.query(Admin).filter(Admin.email == request.new_email).first()
            if existing_admin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already registered"
                )
                
    if request.new_password or request.confirm_password:
        if not (request.new_password and request.confirm_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both new_password and confirm_password must be provided"
            )
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password confirmation does not match"
            )
        if len(request.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )

    if request.new_email:
        admin.email = request.new_email
    if request.new_password:
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
