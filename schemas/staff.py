from pydantic import BaseModel, EmailStr
from typing import Optional

class StaffProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

class StaffAddressEmailUpdate(BaseModel):
    email: Optional[EmailStr] = None
    address: Optional[str] = None
