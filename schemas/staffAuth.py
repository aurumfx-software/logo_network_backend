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
    guardian_contact_number: Optional[str] = None
    aadhaar_number: Optional[str] = None
    aadhaar_front_image: Optional[str] = None
    aadhaar_back_image: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None

    class Config:
        from_attributes = True
