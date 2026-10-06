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

class AdminProfileUpdateRequest(BaseModel):
    new_email: EmailStr
    confirm_email: EmailStr
    new_password: str
    confirm_password: str
