import os
import random
import uuid
from typing import Optional, List
from pydantic import EmailStr
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from database_models import Business, Staff
from schemas.business import BusinessResponse
from utils.dependencies import get_current_staff
from utils.spaces import upload_business_image, delete_business_image

router = APIRouter(prefix="/businesses", tags=[" Field staff - Bussiness Management"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


# create bussiness API

@router.post("/", response_model=BusinessResponse)
def create_business(
    owner_name: Optional[str] = Form(None),
    owner_phone: Optional[str] = Form(None),
    alternate_phone: Optional[str] = Form(None),
    email: Optional[EmailStr] = Form(None),
    address: str = Form(...),
    state: str = Form(...),
    district: str = Form(...),
    city: str = Form(...),
    pincode: str = Form(...),
    business_name: str = Form(...),
    business_type: Optional[str] = Form(None),
    business_category: str = Form(...),
    business_description: Optional[str] = Form(None),
    year_established: Optional[int] = Form(None),
    location_link: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    image_url = None
    if image:
        file_extension = os.path.splitext(image.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid image format. Allowed formats: jpg, jpeg, png, webp")
        
        image_content = image.file.read()
        if len(image_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Image size exceeds 5MB limit")
        image.file.seek(0)
        
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        image_url = upload_business_image(image.file, unique_filename, image.content_type)

    new_business = Business(
        staff_id=current_staff.staff_id,
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
        year_established=year_established,
        location_link=location_link
    )

    try:
        db.add(new_business)
        db.commit()
        db.refresh(new_business)
        return new_business
    except Exception:
        db.rollback()
        raise

# get all bussinesses API
@router.get("/", response_model=List[BusinessResponse])
def get_all_businesses(
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    businesses = db.query(Business).filter(Business.staff_id == current_staff.staff_id).all()
    return businesses

# get bussiness by id API
@router.get("/{id}", response_model=BusinessResponse)
def get_business(
    id: int,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    business = db.query(Business).filter(
        Business.id == id,
        Business.staff_id == current_staff.staff_id
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    return business

# update bussiness API
@router.put("/{id}", response_model=BusinessResponse)
def update_business(
    id: int,
    owner_name: Optional[str] = Form(None),
    owner_phone: Optional[str] = Form(None),
    alternate_phone: Optional[str] = Form(None),
    email: Optional[EmailStr] = Form(None),
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
    location_link: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    business = db.query(Business).filter(
        Business.id == id,
        Business.staff_id == current_staff.staff_id
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

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
    if location_link is not None: business.location_link = location_link

    if image:
        file_extension = os.path.splitext(image.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid image format. Allowed formats: jpg, jpeg, png, webp")
        
        image_content = image.file.read()
        if len(image_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Image size exceeds 5MB limit")
        image.file.seek(0)
        
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Upload new before deleting old
        new_image_url = upload_business_image(image.file, unique_filename, image.content_type)
        
        # Delete old
        if business.image:
            delete_business_image(business.image)
            
        business.image = new_image_url

    try:
        db.commit()
        db.refresh(business)
        return business
    except Exception:
        db.rollback()
        raise

# delete bussiness API
@router.delete("/{id}")
def delete_business(
    id: int,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    business = db.query(Business).filter(
        Business.id == id,
        Business.staff_id == current_staff.staff_id
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
        
    if business.image:
        delete_business_image(business.image)
        
    db.delete(business)
    db.commit()
    
    return {"message": "Business deleted successfully"}
