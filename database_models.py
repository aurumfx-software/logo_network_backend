from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    guardian_contact_number = Column(String, nullable=True)
    address = Column(String, nullable=False)
    role = Column(String, default="staff")
    status = Column(String, default="Active", nullable=False)
    is_active = Column(Boolean, default=True)
    
    # KYC Details
    kyc_status = Column(String, nullable=True)
    aadhaar_number = Column(String, nullable=True)
    aadhaar_front_image = Column(String, nullable=True)
    aadhaar_back_image = Column(String, nullable=True)
    state = Column(String, nullable=True)
    district = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(String, index=True, nullable=True)
    
    owner_name = Column(String, nullable=True)
    owner_phone = Column(String, nullable=True)
    alternate_phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=False)
    state = Column(String, nullable=False)
    district = Column(String, nullable=False)
    city = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    
    business_name = Column(String, nullable=False)
    image = Column(String, nullable=True)
    business_type = Column(String, nullable=True)
    business_category = Column(String, nullable=False)
    business_description = Column(String, nullable=True)
    year_established = Column(Integer, nullable=True)
    location_link = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="admin", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    field_staff_id = Column(Integer, ForeignKey("staff.id"), index=True, nullable=False)
    admin_id = Column(Integer, ForeignKey("admins.id"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    field_staff = relationship("Staff", foreign_keys=[field_staff_id])
    admin = relationship("Admin", foreign_keys=[admin_id])

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True, nullable=False)
    sender_id = Column(Integer, index=True, nullable=False)
    sender_role = Column(String, nullable=False)
    receiver_id = Column(Integer, index=True, nullable=False)
    receiver_role = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", backref="messages")

class KYCSubmission(Base):
    __tablename__ = "kyc_submissions"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), index=True, nullable=False)
    aadhaar_front_image = Column(String, nullable=True)
    aadhaar_back_image = Column(String, nullable=True)
    status = Column(String, default="PENDING", nullable=False)
    rejection_reason = Column(String, nullable=True)
    reviewer_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    staff = relationship("Staff", backref="kyc_submissions")
    reviewer = relationship("Admin")

