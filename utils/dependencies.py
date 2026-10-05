from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from database import get_db
from database_models import Staff, Admin
from utils.jwt import SECRET_KEY, ALGORITHM

security = HTTPBearer()

def get_current_staff(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> Staff:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        staff_id: str = payload.get("sub")
        if staff_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    staff = db.query(Staff).filter(Staff.staff_id == staff_id).first()
    if staff is None or not staff.is_active or staff.status != "Active":
        raise credentials_exception
    return staff

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> Admin:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: str = payload.get("sub")
        role: str = payload.get("role")
        if admin_id is None or role != "admin":
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    admin = db.query(Admin).filter(Admin.id == int(admin_id)).first()
    if admin is None or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive admin or insufficient privileges"
        )
    return admin
