from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from database import get_db
from database_models import Business
from schemas.customer import CustomerBusinessResponse

router = APIRouter(prefix="/customer", tags=["Customer API - Public TO GET  BUSSINESS "])

@router.get("/businesses", response_model=CustomerBusinessResponse)
def get_customer_businesses(
    state: Optional[str] = None,
    district: Optional[str] = None,
    location: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Business)

    if state:
        state_filter = f"%{state}%"
        query = query.filter(Business.state.ilike(state_filter))

    if district:
        district_filter = f"%{district}%"
        query = query.filter(Business.district.ilike(district_filter))

    if location:
        location_filter = f"%{location}%"
        query = query.filter(
            or_(
                Business.address.ilike(location_filter),
                Business.city.ilike(location_filter),
                Business.pincode.ilike(location_filter)
            )
        )

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Business.business_name.ilike(search_filter),
                Business.business_category.ilike(search_filter),
                Business.business_type.ilike(search_filter),
                Business.address.ilike(search_filter),
                Business.city.ilike(search_filter)
            )
        )

    query = query.order_by(Business.created_at.desc())
    results = query.all()

    return {
        "businesses": results,
        "total": len(results)
    }
