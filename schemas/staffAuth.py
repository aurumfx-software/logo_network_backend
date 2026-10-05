from pydantic import BaseModel, EmailStr
from typing import Optional

class StaffRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str
    address: str

class StaffLoginRequest(BaseModel):
    staff_id: str
    password: str

class StaffResponse(BaseModel):
    id: int
    staff_id: str
    name: str
    email: str
    phone: str
    address: str
    role: str

    class Config:
        from_attributes = True
