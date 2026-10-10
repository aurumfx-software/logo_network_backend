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

class AdminForgotPasswordRequest(BaseModel):
    email: EmailStr

class AdminVerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    reset_request_id: str

class AdminResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str
    confirm_password: str
