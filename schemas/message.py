from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MessageCreate(BaseModel):
    message: str

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_role: str
    receiver_id: int
    receiver_role: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class ConversationResponse(BaseModel):
    conversation_id: int
    field_staff_id: int
    field_staff_name: str
    admin_id: int
    total_message_count: int
    unread_count: int
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None

class StaffConversationResponse(BaseModel):
    conversation_id: int
    field_staff_id: int
    field_staff_name: str
    admin_id: int
    total_message_count: int
    unread_count: int
    messages: List[MessageResponse] = []

class UnreadCountResponse(BaseModel):
    unread_count: int

class MarkReadResponse(BaseModel):
    success: bool
    unread_count: int
