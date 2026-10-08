from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, engine, Base
import database_models
from routers import staffAuth, StaffBussinessManagement, adminAuth, AdminStaffManagement, AdminBussninessManagement, AdminStaffProfileManagement

database_models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fast Api Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(staffAuth.router)
app.include_router(adminAuth.router)
app.include_router(AdminStaffManagement.router)
app.include_router(AdminBussninessManagement.router)
app.include_router(AdminStaffProfileManagement.router)

from routers import AdminStaffReport
app.include_router(AdminStaffReport.router)

from routers import AdminDashboard
app.include_router(AdminDashboard.router)

from routers import AdminProfileManagement
app.include_router(AdminProfileManagement.router)

from routers import StafProfileManagement
app.include_router(StafProfileManagement.router)

# Business routers
app.include_router(StaffBussinessManagement.router)

# Dashboard router
from routers import StaffDashboard
app.include_router(StaffDashboard.router)

# Customer router
from routers import customer
app.include_router(customer.router)

# Messages router
from routers import messages
app.include_router(messages.router)


@app.get("/")
def read_root():
    return {"message": "Field Staff Backend is running"}

@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception as e:
        return {"database": "connection failed", "error": str(e)}
