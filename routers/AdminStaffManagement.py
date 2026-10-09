import os
import uuid
import secrets
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import get_db
from database_models import Admin, Staff, Business, KYCSubmission
from utils.dependencies import get_current_admin
from utils.spaces import upload_business_image, delete_business_image, upload_staff_image
from schemas.admin import StaffAdminResponse, StaffListResponse, StaffStatusUpdateRequest, StaffStatusUpdateResponse, BusinessListResponse, AdminStaffProfileUpdate
from schemas.business import BusinessResponse
from utils.password import hash_password
from schemas.staffAuth import StaffResponse

router = APIRouter(prefix="/admin")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@router.get("/staff", response_model=StaffListResponse, tags=["Admin Staff Management"])
def admin_get_staff(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    staff_list = db.query(Staff).all()
    businesses = db.query(Business).all()
    
    business_map = {}
    for b in businesses:
        if b.staff_id:
            if b.staff_id not in business_map:
                business_map[b.staff_id] = []
            business_map[b.staff_id].append(b)
            
    result = []
    for staff in staff_list:
        staff_businesses = business_map.get(staff.staff_id, [])
        result.append({
            "id": staff.id,
            "staff_id": staff.staff_id,
            "name": staff.name,
            "email": staff.email,
            "phone": staff.phone,
            "guardian_contact_number": staff.guardian_contact_number,
            "address": staff.address,
            "role": staff.role,
            "status": staff.status,
            "aadhaar_number": staff.aadhaar_number,
            "aadhaar_front_image": staff.aadhaar_front_image,
            "aadhaar_back_image": staff.aadhaar_back_image,
            "state": staff.state,
            "district": staff.district,
            "created_at": staff.created_at,
            "businesses": staff_businesses,
            "total_businesses": len(staff_businesses)
        })
        
    return {"staff": result, "total": len(result)}

def generate_staff_id(db: Session) -> str:
    while True:
        rand_digits = f"{secrets.randbelow(1000):03d}"
        new_id = f"SF{rand_digits}"
        if not db.query(Staff).filter(Staff.staff_id == new_id).first():
            return new_id

@router.post("/staff/register", tags=["Admin Staff Management"])
def admin_register_staff(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form(...),
    guardian_contact_number: str = Form(...),
    address: str = Form(...),
    aadhaar_number: str = Form(...),
    state: str = Form(...),
    district: str = Form(...),
    aadhaar_front_image: Optional[UploadFile] = File(None),
    aadhaar_back_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db), 
    admin: Admin = Depends(get_current_admin)
):
    # Validate Name
    if any(char.islower() for char in name if char.isalpha()):
        raise HTTPException(status_code=422, detail="Field Staff name must be entered in uppercase letters.")

    # Validate Aadhaar Number
    normalized_aadhaar = aadhaar_number.replace(" ", "").replace("-", "")
    if not normalized_aadhaar.isdigit() or len(normalized_aadhaar) != 12:
        raise HTTPException(status_code=422, detail="Aadhaar number must be exactly 12 digits")
        
    if not state.strip():
        raise HTTPException(status_code=422, detail="State is required")
        
    if not district.strip():
        raise HTTPException(status_code=422, detail="District is required")

    if db.query(Staff).filter(Staff.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(Staff).filter(Staff.phone == phone).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    front_url = None
    if aadhaar_front_image and aadhaar_front_image.filename:
        ext_front = os.path.splitext(aadhaar_front_image.filename)[1].lower()
        if ext_front not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=422, detail="Invalid front image format")
        front_filename = f"{uuid.uuid4().hex}_front{ext_front}"
        try:
            front_url = upload_staff_image(aadhaar_front_image.file, front_filename, aadhaar_front_image.content_type)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    back_url = None
    if aadhaar_back_image and aadhaar_back_image.filename:
        ext_back = os.path.splitext(aadhaar_back_image.filename)[1].lower()
        if ext_back not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=422, detail="Invalid back image format")
        back_filename = f"{uuid.uuid4().hex}_back{ext_back}"
        try:
            back_url = upload_staff_image(aadhaar_back_image.file, back_filename, aadhaar_back_image.content_type)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    from sqlalchemy.exc import IntegrityError
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            staff_id = generate_staff_id(db)
            
            if front_url and back_url:
                staff_kyc_status = "APPROVED"
            else:
                staff_kyc_status = "PENDING"
                
            new_staff = Staff(
                staff_id=staff_id,
                name=name,
                email=email,
                password_hash=hash_password(password),
                phone=phone,
                guardian_contact_number=guardian_contact_number,
                address=address,
                aadhaar_number=normalized_aadhaar,
                aadhaar_front_image=front_url,
                aadhaar_back_image=back_url,
                state=state,
                district=district,
                kyc_status=staff_kyc_status
            )
            
            db.add(new_staff)
            db.commit()
            db.refresh(new_staff)
            
            if staff_kyc_status == "APPROVED":
                from sqlalchemy.sql import func
                new_kyc = KYCSubmission(
                    staff_id=new_staff.id,
                    aadhaar_front_image=front_url,
                    aadhaar_back_image=back_url,
                    status="APPROVED",
                    reviewer_id=admin.id,
                    reviewed_at=func.now()
                )
                db.add(new_kyc)
                db.commit()
            elif front_url or back_url:
                new_kyc = KYCSubmission(
                    staff_id=new_staff.id,
                    aadhaar_front_image=front_url,
                    aadhaar_back_image=back_url,
                    status="PENDING"
                )
                db.add(new_kyc)
                db.commit()
            
            
            return {
                "message": "Field Staff created successfully",
                "staff_id": new_staff.staff_id,
                "user_id": new_staff.id,
                "name": new_staff.name,
                "email": new_staff.email,
                "phone": new_staff.phone,
                "guardian_contact_number": new_staff.guardian_contact_number,
                "aadhaar_number": new_staff.aadhaar_number,
                "aadhaar_front_image": new_staff.aadhaar_front_image,
                "aadhaar_back_image": new_staff.aadhaar_back_image,
                "state": new_staff.state,
                "district": new_staff.district
            }
        except IntegrityError:
            db.rollback()
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail="Failed to generate a unique staff ID. Please try again.")

@router.get("/staff/search/{staff_id}", response_model=StaffAdminResponse, tags=["Admin Staff Management"])
def admin_search_staff_by_id(staff_id: str, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    staff = db.query(Staff).filter(Staff.staff_id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
        
    businesses = db.query(Business).filter(Business.staff_id == staff.staff_id).all()
    
    return {
        "id": staff.id,
        "staff_id": staff.staff_id,
        "name": staff.name,
        "email": staff.email,
        "phone": staff.phone,
        "guardian_contact_number": staff.guardian_contact_number,
        "address": staff.address,
        "role": staff.role,
        "status": staff.status,
        "aadhaar_number": staff.aadhaar_number,
        "aadhaar_front_image": staff.aadhaar_front_image,
        "aadhaar_back_image": staff.aadhaar_back_image,
        "state": staff.state,
        "district": staff.district,
        "created_at": staff.created_at,
        "businesses": businesses,
        "total_businesses": len(businesses)
    }

@router.get("/staff/print", tags=["Admin Staff Management"])
def admin_print_staff(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    staff_list = db.query(Staff).filter(Staff.role == "staff").order_by(Staff.staff_id.asc()).all()
    
    if not staff_list:
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Field Staff Details Report</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
            </style>
        </head>
        <body>
            <h2>No Field Staff records found.</h2>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    rows_html = ""
    for idx, s in enumerate(staff_list, 1):
        guardian = s.guardian_contact_number if s.guardian_contact_number else "—"
        state = s.state if s.state else "—"
        district = s.district if s.district else "—"
        
        rows_html += f"""
        <tr>
            <td>{idx}</td>
            <td>{s.staff_id}</td>
            <td>{s.name}</td>
            <td>{s.email}</td>
            <td>{s.phone}</td>
            <td>{guardian}</td>
            <td>{state}</td>
            <td>{district}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Field Staff Details Report</title>
        <style>
            @page {{
                size: A4 landscape;
                margin: 10mm;
            }}
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 10mm;
                color: #000;
                font-size: 12px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 20px;
                text-transform: uppercase;
            }}
            .data-table {{
                width: 100%;
                border-collapse: collapse;
            }}
            .data-table th, .data-table td {{
                border: 1px solid #000;
                padding: 8px 6px;
                text-align: left;
            }}
            .data-table th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            thead {{
                display: table-header-group;
            }}
            tr {{
                page-break-inside: avoid;
            }}
            .print-btn {{
                display: block;
                margin: 0 auto 20px auto;
                padding: 10px 20px;
                font-size: 14px;
                cursor: pointer;
            }}
            @media print {{
                body {{
                    padding: 0;
                }}
                .print-btn {{
                    display: none;
                }}
                body {{
                    -webkit-print-color-adjust: exact;
                    print-color-adjust: exact;
                }}
            }}
        </style>
    </head>
    <body>
        <button onclick="window.print()" class="print-btn">Print Report</button>
        <div class="header">
            <h1>FIELD STAFF DETAILS REPORT</h1>
        </div>
        
        <table class="data-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Staff ID</th>
                    <th>Staff Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Guardian Contact Number</th>
                    <th>State</th>
                    <th>District</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/staff/{id}", response_model=StaffAdminResponse, tags=["Admin Staff Management"])
def admin_get_one_staff(id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    staff = db.query(Staff).filter(Staff.id == id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
        
    businesses = db.query(Business).filter(Business.staff_id == staff.staff_id).all()
    
    return {
        "id": staff.id,
        "staff_id": staff.staff_id,
        "name": staff.name,
        "email": staff.email,
        "phone": staff.phone,
        "guardian_contact_number": staff.guardian_contact_number,
        "address": staff.address,
        "role": staff.role,
        "status": staff.status,
        "aadhaar_number": staff.aadhaar_number,
        "aadhaar_front_image": staff.aadhaar_front_image,
        "aadhaar_back_image": staff.aadhaar_back_image,
        "state": staff.state,
        "district": staff.district,
        "created_at": staff.created_at,
        "businesses": businesses,
        "total_businesses": len(businesses)
    }

@router.patch("/staff/{id}/status", response_model=StaffStatusUpdateResponse, tags=["Admin Staff Management"])
def admin_update_staff_status(id: int, request: StaffStatusUpdateRequest, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    if request.status not in ["Active", "Deactivate"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be 'Active' or 'Deactivate'")
    
    staff = db.query(Staff).filter(Staff.id == id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    staff.status = request.status
    db.commit()
    db.refresh(staff)
    
    return {
        "message": f"Staff {'activated' if request.status == 'Active' else 'deactivated'} successfully",
        "staff": staff
    }
