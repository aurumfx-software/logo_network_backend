from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database_models import Admin
from schemas.adminAuth import AdminLogin, AdminLoginResponse
from utils.password import verify_password
from utils.jwt import create_access_token

router = APIRouter(prefix="/admin-auth", tags=["Admin Authentication"])

@router.post("/login", response_model=AdminLoginResponse)
def admin_login(login_data: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == login_data.email).first()
    
    if not admin or not verify_password(login_data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is not active"
        )
        
    access_token = create_access_token(data={"sub": str(admin.id), "role": admin.role})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": admin
    }
