from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class BusinessResponse(BaseModel):
    id: int
    staff_id: Optional[str] = None
    owner_name: str
    owner_phone: str
    alternate_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: str
    state: str
    district: str
    city: str
    pincode: str
    business_name: str
    image: Optional[str] = None
    business_type: str
    business_category: str
    business_description: Optional[str] = None
    year_established: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True




