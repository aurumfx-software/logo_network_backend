import os
import random
import uuid
from typing import Optional, List
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
        staff_id=current_staff.id,
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

# get all bussinesses API
@router.get("/", response_model=List[BusinessResponse])
def get_all_businesses(
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    businesses = db.query(Business).filter(Business.staff_id == current_staff.id).all()
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
        Business.staff_id == current_staff.id
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    return business

# update bussiness API
@router.put("/{id}", response_model=BusinessResponse)
def update_business(
    id: int,
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
    current_staff: Staff = Depends(get_current_staff)
):
    business = db.query(Business).filter(
        Business.id == id,
        Business.staff_id == current_staff.id
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    business.owner_name = owner_name
    business.owner_phone = owner_phone
    business.alternate_phone = alternate_phone
    business.email = email
    business.address = address
    business.state = state
    business.district = district
    business.city = city
    business.pincode = pincode
    business.business_name = business_name
    business.business_type = business_type
    business.business_category = business_category
    business.business_description = business_description
    business.year_established = year_established

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

    db.commit()
    db.refresh(business)

    return business

# delete bussiness API
@router.delete("/{id}")
def delete_business(
    id: int,
    db: Session = Depends(get_db),
    current_staff: Staff = Depends(get_current_staff)
):
    business = db.query(Business).filter(
        Business.id == id,
        Business.staff_id == current_staff.id
    ).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
        
    if business.image:
        delete_business_image(business.image)
        
    db.delete(business)
    db.commit()
    
    return {"message": "Business deleted successfully"}
