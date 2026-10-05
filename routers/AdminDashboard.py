from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, time, date, timedelta, timezone
from typing import List

from database import get_db
from database_models import Staff, Business
from utils.dependencies import get_current_admin
from schemas.dashboard import AdminDashboardSummaryResponse

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])
 
 
@router.get("/dashboard/summary", response_model=AdminDashboardSummaryResponse)
def get_admin_dashboard_summary(
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    # 1. Summary
    total_staff = db.query(func.count(Staff.id)).scalar() or 0
    active_staff = db.query(func.count(Staff.id)).filter(Staff.status == "Active").scalar() or 0
    deactivated_staff = db.query(func.count(Staff.id)).filter(Staff.status == "Deactivate").scalar() or 0
    total_businesses = db.query(func.count(Business.id)).scalar() or 0

    # 2. Businesses Growth
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    week_start = datetime.combine(now.date() - timedelta(days=now.weekday()), time.min, tzinfo=timezone.utc)
    month_start = datetime.combine(date(now.year, now.month, 1), time.min, tzinfo=timezone.utc)
    year_start = datetime.combine(date(now.year, 1, 1), time.min, tzinfo=timezone.utc)

    today_count = db.query(func.count(Business.id)).filter(Business.created_at >= today_start).scalar() or 0
    this_week_count = db.query(func.count(Business.id)).filter(Business.created_at >= week_start).scalar() or 0
    this_month_count = db.query(func.count(Business.id)).filter(Business.created_at >= month_start).scalar() or 0
    this_year_count = db.query(func.count(Business.id)).filter(Business.created_at >= year_start).scalar() or 0

    # 3. Categories
    category_counts = db.query(
        Business.business_category, 
        func.count(Business.id).label('count')
    ).filter(
        Business.business_category.isnot(None), 
        Business.business_category != ""
    ).group_by(Business.business_category).order_by(func.count(Business.id).desc()).all()
    categories = [{"category": c[0], "count": c[1]} for c in category_counts]

    # 4. States
    state_counts = db.query(
        Business.state, 
        func.count(Business.id).label('count')
    ).filter(
        Business.state.isnot(None), 
        Business.state != ""
    ).group_by(Business.state).order_by(func.count(Business.id).desc()).all()
    states = [{"state": c[0], "count": c[1]} for c in state_counts]

    # 5. Districts
    district_counts = db.query(
        Business.district, 
        func.count(Business.id).label('count')
    ).filter(
        Business.district.isnot(None), 
        Business.district != ""
    ).group_by(Business.district).order_by(func.count(Business.id).desc()).all()
    districts = [{"district": c[0], "count": c[1]} for c in district_counts]

    # 6. Locations (City)
    location_counts = db.query(
        Business.city, 
        func.count(Business.id).label('count')
    ).filter(
        Business.city.isnot(None), 
        Business.city != ""
    ).group_by(Business.city).order_by(func.count(Business.id).desc()).all()
    locations = [{"location": c[0], "count": c[1]} for c in location_counts]

    return {
        "summary": {
            "total_staff": total_staff,
            "active_staff": active_staff,
            "deactivated_staff": deactivated_staff,
            "total_businesses": total_businesses
        },
        "businesses": {
            "today": today_count,
            "this_week": this_week_count,
            "this_month": this_month_count,
            "this_year": this_year_count
        },
        "business_categories": categories,
        "states": states,
        "districts": districts,
        "locations": locations
    }
