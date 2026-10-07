from pydantic import BaseModel, EmailStr

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class AdminResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str
    admin: AdminResponse

from typing import Optional

class AdminProfileUpdateRequest(BaseModel):
    new_email: Optional[EmailStr] = None
    confirm_email: Optional[EmailStr] = None
    new_password: Optional[str] = None
    confirm_password: Optional[str] = None
