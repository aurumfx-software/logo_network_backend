import os
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from database import get_db
from database_models import Admin, Staff, Business
from utils.dependencies import get_current_admin
from utils.spaces import upload_business_image, delete_business_image
from schemas.admin import StaffAdminResponse, StaffListResponse, StaffStatusUpdateRequest, StaffStatusUpdateResponse, BusinessListResponse
from schemas.business import BusinessResponse

router = APIRouter(prefix="/admin")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB



@router.post("/businesses", response_model=BusinessResponse, tags=["Admin Business Management"])
def admin_create_business(
    staff_id: Optional[str] = Form(None),
    owner_name: str = Form(...),
    owner_phone: str = Form(...),
    alternate_phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    address: str = Form(...),
    state: str = Form(...),
    district: str = Form(...),
    city: str = Form(...),
    pincode: str = Form(...),
    business_name: str = Form(...),
    business_type: str = Form(...),
    business_category: str = Form(...),
    business_description: Optional[str] = Form(None),
    year_established: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    if staff_id is not None:
        staff = db.query(Staff).filter(Staff.staff_id == staff_id).first()
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")

    image_url = None
    if image:
        file_extension = os.path.splitext(image.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid image format")
        image_content = image.file.read()
        if len(image_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Image size exceeds 5MB")
        image.file.seek(0)
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        image_url = upload_business_image(image.file, unique_filename, image.content_type)

    new_business = Business(
        staff_id=staff_id,
        owner_name=owner_name,
        owner_phone=owner_phone,
        alternate_phone=alternate_phone,
        email=email,
        address=address,
        state=state,
        district=district,
        city=city,
        pincode=pincode,
        business_name=business_name,
        image=image_url,
        business_type=business_type,
        business_category=business_category,
        business_description=business_description,
        year_established=year_established
    )
    db.add(new_business)
    db.commit()
    db.refresh(new_business)
    return new_business

@router.get("/businesses", response_model=BusinessListResponse, tags=["Admin Business Management"])
def admin_get_businesses(
    district: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    staff_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    query = db.query(Business)
    
    if district:
        query = query.filter(Business.district.ilike(f"%{district}%"))
    if state:
        query = query.filter(Business.state.ilike(f"%{state}%"))
    if city:
        query = query.filter(Business.city.ilike(f"%{city}%"))
    if category:
        query = query.filter(Business.business_category.ilike(f"%{category}%"))
    if staff_id:
        query = query.filter(Business.staff_id == staff_id)
    if search:
        query = query.filter(Business.business_name.ilike(f"%{search}%"))
        
    businesses = query.all()
    return {"businesses": businesses, "total": len(businesses)}

@router.get("/businesses/{id}", response_model=BusinessResponse, tags=["Admin Business Management"])
def admin_get_one_business(id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    business = db.query(Business).filter(Business.id == id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business

@router.put("/businesses/{id}", response_model=BusinessResponse, tags=["Admin Business Management"])
def admin_update_business(
    id: int,
    staff_id: Optional[str] = Form(None),
    owner_name: Optional[str] = Form(None),
    owner_phone: Optional[str] = Form(None),
    alternate_phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    district: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    pincode: Optional[str] = Form(None),
    business_name: Optional[str] = Form(None),
    business_type: Optional[str] = Form(None),
    business_category: Optional[str] = Form(None),
    business_description: Optional[str] = Form(None),
    year_established: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    business = db.query(Business).filter(Business.id == id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
        
    if staff_id is not None:
        staff = db.query(Staff).filter(Staff.staff_id == staff_id).first()
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        business.staff_id = staff_id

    if owner_name is not None: business.owner_name = owner_name
    if owner_phone is not None: business.owner_phone = owner_phone
    if alternate_phone is not None: business.alternate_phone = alternate_phone
    if email is not None: business.email = email
    if address is not None: business.address = address
    if state is not None: business.state = state
    if district is not None: business.district = district
    if city is not None: business.city = city
    if pincode is not None: business.pincode = pincode
    if business_name is not None: business.business_name = business_name
    if business_type is not None: business.business_type = business_type
    if business_category is not None: business.business_category = business_category
    if business_description is not None: business.business_description = business_description
    if year_established is not None: business.year_established = year_established
    
    if image:
        file_extension = os.path.splitext(image.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid image format")
        image_content = image.file.read()
        if len(image_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Image size exceeds 5MB")
        image.file.seek(0)
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        new_image_url = upload_business_image(image.file, unique_filename, image.content_type)
        if business.image:
            delete_business_image(business.image)
        business.image = new_image_url
        
    db.commit()
    db.refresh(business)
    return business

@router.delete("/businesses/{id}", tags=["Admin Business Management"])
def admin_delete_business(id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    business = db.query(Business).filter(Business.id == id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
        
    if business.image:
        delete_business_image(business.image)
        
    db.delete(business)
    db.commit()
    return {"message": "Business deleted successfully"}
