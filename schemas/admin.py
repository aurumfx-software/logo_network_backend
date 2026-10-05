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
    created_at: datetime
    businesses: Optional[List[BusinessResponse]] = []

    class Config:
        from_attributes = True

class StaffListResponse(BaseModel):
    staff: List[StaffAdminResponse]
    total: int

class StaffStatusUpdateRequest(BaseModel):
    status: str

class StaffStatusUpdateResponse(BaseModel):
    message: str
    staff: StaffAdminResponse

class BusinessListResponse(BaseModel):
    businesses: List[BusinessResponse]
    total: int
