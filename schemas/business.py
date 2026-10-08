from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class BusinessResponse(BaseModel):
    id: int
    staff_id: Optional[str] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: str
    state: str
    district: str
    city: str
    pincode: str
    business_name: str
    image: Optional[str] = None
    business_type: Optional[str] = None
    business_category: str
    business_description: Optional[str] = None
    year_established: Optional[int] = None
    location_link: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True




