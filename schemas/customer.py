from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CustomerBusinessItem(BaseModel):
    id: int
    owner_name: Optional[str] = None
    business_name: str
    address: str
    district: str
    city: str
    pincode: str
    image: Optional[str] = None
    business_type: Optional[str] = None
    business_category: str
    business_description: Optional[str] = None
    year_established: Optional[int] = None
    location_link: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CustomerBusinessResponse(BaseModel):
    businesses: List[CustomerBusinessItem]
    total: int
