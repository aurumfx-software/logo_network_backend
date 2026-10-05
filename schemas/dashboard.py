from pydantic import BaseModel
from typing import List
from schemas.business import BusinessResponse

class StaffSummary(BaseModel):
    id: int
    staff_id: str
    name: str
    district: str

class DashboardSummaryStats(BaseModel):
    total_businesses: int
    today_added: int
    this_week_added: int
    this_month_added: int
    this_year_added: int

class CategoryCount(BaseModel):
    category: str
    count: int

class DistrictCount(BaseModel):
    district: str
    count: int

class LocationCount(BaseModel):
    location: str
    count: int

class DashboardSummaryResponse(BaseModel):
    staff: StaffSummary
    summary: DashboardSummaryStats
    business_categories: List[CategoryCount]
    districts: List[DistrictCount]
    locations: List[LocationCount]
    businesses: List[BusinessResponse]

class AdminSummaryData(BaseModel):
    total_staff: int
    active_staff: int
    deactivated_staff: int
    total_businesses: int

class AdminBusinessGrowthData(BaseModel):
    today: int
    this_week: int
    this_month: int
    this_year: int

class StateCount(BaseModel):
    state: str
    count: int

class AdminDashboardSummaryResponse(BaseModel):
    summary: AdminSummaryData
    businesses: AdminBusinessGrowthData
    business_categories: List[CategoryCount]
    states: List[StateCount]
    districts: List[DistrictCount]
    locations: List[LocationCount]
