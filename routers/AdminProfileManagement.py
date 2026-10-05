from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database_models import Admin
from schemas.adminAuth import ChangePasswordRequest
from utils.password import verify_password, hash_password
from utils.dependencies import get_current_admin

router = APIRouter(prefix="/admin-profile", tags=["Admin-profile"])

@router.put("/change-password")
def change_admin_password(
    request: ChangePasswordRequest, 
    db: Session = Depends(get_db), 
    admin: Admin = Depends(get_current_admin)
):
    if not verify_password(request.old_password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid old password"
        )
    
    admin.password_hash = hash_password(request.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}
