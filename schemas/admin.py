from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from schemas.business import BusinessResponse

class StaffAdminResponse(BaseModel):
    id: int
    staff_id: str
    name: str
    email: str
    phone: str
    address: str
    role: str
    status: str
    aadhaar_number: Optional[str] = None
    aadhaar_front_image: Optional[str] = None
    aadhaar_back_image: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    created_at: datetime
    businesses: Optional[List[BusinessResponse]] = []
    total_businesses: Optional[int] = 0

    class Config:
        from_attributes = True

class StaffListResponse(BaseModel):
    staff: List[StaffAdminResponse]
    total: int

class AdminStaffProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    password: Optional[str] = None

class StaffStatusUpdateRequest(BaseModel):
    status: str

class StaffStatusUpdateResponse(BaseModel):
    message: str
    staff: StaffAdminResponse

class BusinessListResponse(BaseModel):
    businesses: List[BusinessResponse]
    total: int
