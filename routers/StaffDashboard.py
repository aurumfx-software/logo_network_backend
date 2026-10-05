from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, time, date, timedelta, timezone
from database import get_db
from database_models import Business, Staff
from schemas.dashboard import DashboardSummaryResponse
from utils.dependencies import get_current_staff

router = APIRouter(prefix="/staff/dashboard", tags=[" Field staff - Business-Dashboard"])

# Business Dashboard Summary API
@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    week_start = datetime.combine(now.date() - timedelta(days=now.weekday()), time.min, tzinfo=timezone.utc)
    month_start = datetime.combine(date(now.year, now.month, 1), time.min, tzinfo=timezone.utc)
    year_start = datetime.combine(date(now.year, 1, 1), time.min, tzinfo=timezone.utc)

    # 1. Staff Section
    staff_summary = {
        "id": current_staff.id,
        "staff_id": current_staff.staff_id,
        "name": current_staff.name,
        "district": current_staff.district
    }

    # 2. Businesses and summary stats
    all_businesses = db.query(Business).filter(
        Business.staff_id == current_staff.id
    ).order_by(Business.created_at.desc()).all()

    total_businesses = len(all_businesses)
    
    today_added = 0
    this_week_added = 0
    this_month_added = 0
    this_year_added = 0
    
    cat_counts = {}
    dist_counts = {}
    loc_counts = {}

    for b in all_businesses:
        if b.created_at:
            # Handle naive datetime if database returns naive UTC
            created_at = b.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
                
            if created_at >= today_start:
                today_added += 1
            if created_at >= week_start:
                this_week_added += 1
            if created_at >= month_start:
                this_month_added += 1
            if created_at >= year_start:
                this_year_added += 1
                
        # Category Count
        cat = b.business_category
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        
        # District Count
        dist = b.district
        dist_counts[dist] = dist_counts.get(dist, 0) + 1
        
        # Location (city) Count
        loc = b.city
        if loc:
            loc_counts[loc] = loc_counts.get(loc, 0) + 1

    summary_stats = {
        "total_businesses": total_businesses,
        "today_added": today_added,
        "this_week_added": this_week_added,
        "this_month_added": this_month_added,
        "this_year_added": this_year_added
    }

    business_categories = [{"category": k, "count": v} for k, v in cat_counts.items()]
    districts = [{"district": k, "count": v} for k, v in dist_counts.items()]
    locations = [{"location": k, "count": v} for k, v in loc_counts.items()]

    return {
        "staff": staff_summary,
        "summary": summary_stats,
        "business_categories": business_categories,
        "districts": districts,
        "locations": locations,
        "businesses": all_businesses
    }
