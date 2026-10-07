from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List
import json
import jwt

from database import get_db
from database_models import Staff, Admin, Conversation, Message as DBMessage
from schemas.message import MessageCreate, MessageResponse, ConversationResponse, StaffConversationResponse, UnreadCountResponse
from utils.websocket_manager import manager
from utils.jwt import SECRET_KEY, ALGORITHM
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

router = APIRouter(prefix="/api/messages")
security = HTTPBearer()

def get_current_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if "role" in payload and payload["role"] == "admin":
            admin_id = int(payload.get("sub"))
            admin = db.query(Admin).filter(Admin.id == admin_id).first()
            if not admin or not admin.is_active:
                return None
            return {"id": admin.id, "role": "admin", "user": admin}
        else:
            staff_id = payload.get("id")
            if not staff_id:
                return None
            staff = db.query(Staff).filter(Staff.id == staff_id).first()
            if not staff or not staff.is_active:
                return None
            return {"id": staff.id, "role": "staff", "user": staff}
    except Exception:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user_info = get_current_user_from_token(credentials.credentials, db)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_info

def get_unread_count_for_user(user_id: int, role: str, db: Session) -> int:
    return db.query(DBMessage).filter(
        DBMessage.receiver_id == user_id,
        DBMessage.receiver_role == role,
        DBMessage.is_read == False
    ).count()


# --- Field Staff - Messages ---

@router.post("/send", response_model=MessageResponse, tags=["Field Staff - Messages"])
async def send_message(msg_data: MessageCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "staff":
        raise HTTPException(status_code=403, detail="Only Field Staff can use this endpoint")
        
    sender_id = current_user["id"]
    sender_role = "staff"
    
    receiver = db.query(Admin).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Admin not found")
        
    receiver_id = receiver.id
    receiver_role = "admin"
    
    admin_id = receiver_id
    staff_id = sender_id

    conversation = db.query(Conversation).filter(
        Conversation.admin_id == admin_id,
        Conversation.field_staff_id == staff_id
    ).first()
    
    if not conversation:
        conversation = Conversation(admin_id=admin_id, field_staff_id=staff_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    else:
        db.query(DBMessage).filter(
            DBMessage.conversation_id == conversation.id,
            DBMessage.receiver_id == sender_id,
            DBMessage.receiver_role == sender_role,
            DBMessage.is_read == False
        ).update({"is_read": True})
        db.commit()
        
    new_msg = DBMessage(
        conversation_id=conversation.id,
        sender_id=sender_id,
        sender_role=sender_role,
        receiver_id=receiver_id,
        receiver_role=receiver_role,
        message=msg_data.message,
        is_read=False
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    
    msg_response = MessageResponse.model_validate(new_msg)
    
    # Websocket notification
    await manager.send_to_user(receiver_id, receiver_role, {
        "type": "new_message",
        "message": msg_response.model_dump(mode="json")
    })
    
    receiver_unread_count = get_unread_count_for_user(receiver_id, receiver_role, db)
    await manager.send_to_user(receiver_id, receiver_role, {
        "type": "unread_count",
        "unread_count": receiver_unread_count
    })
    
    await manager.send_to_user(sender_id, sender_role, {
        "type": "new_message",
        "message": msg_response.model_dump(mode="json")
    })

    return msg_response

@router.get("/my", response_model=List[StaffConversationResponse], tags=["Field Staff - Messages"])
def get_my_conversations(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "staff":
        raise HTTPException(status_code=403, detail="Only Field Staff can use this endpoint")
        
    user_id = current_user["id"]
    role = "staff"
    
    conversations = db.query(Conversation).filter(Conversation.field_staff_id == user_id).all()
        
    result = []
    for conv in conversations:
        messages = db.query(DBMessage).filter(DBMessage.conversation_id == conv.id).order_by(DBMessage.created_at.asc()).all()
        
        unread = db.query(DBMessage).filter(
            DBMessage.conversation_id == conv.id,
            DBMessage.receiver_id == user_id,
            DBMessage.receiver_role == role,
            DBMessage.is_read == False
        ).count()
        
        total_msg_count = len(messages)
        
        result.append(StaffConversationResponse(
            conversation_id=conv.id,
            field_staff_id=conv.field_staff_id,
            field_staff_name=current_user["user"].name,
            admin_id=conv.admin_id,
            total_message_count=total_msg_count,
            unread_count=unread,
            messages=messages
        ))
        
    return result


# --- Admin - Messages ---

@router.get("/conversations", response_model=List[ConversationResponse], tags=["Admin - Messages"])
def get_all_conversations(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only Admin can use this endpoint")
        
    user_id = current_user["id"]
    role = "admin"
    
    conversations = db.query(Conversation).filter(Conversation.admin_id == user_id).all()
        
    result = []
    for conv in conversations:
        last_msg = db.query(DBMessage).filter(DBMessage.conversation_id == conv.id).order_by(desc(DBMessage.created_at)).first()
        
        unread = db.query(DBMessage).filter(
            DBMessage.conversation_id == conv.id,
            DBMessage.receiver_id == user_id,
            DBMessage.receiver_role == role,
            DBMessage.is_read == False
        ).count()
        
        total_msg_count = db.query(DBMessage).filter(DBMessage.conversation_id == conv.id).count()
        
        staff_name = conv.field_staff.name if conv.field_staff else "Unknown"
        
        result.append(ConversationResponse(
            conversation_id=conv.id,
            field_staff_id=conv.field_staff_id,
            field_staff_name=staff_name,
            admin_id=conv.admin_id,
            total_message_count=total_msg_count,
            unread_count=unread,
            last_message=last_msg.message if last_msg else None,
            last_message_at=last_msg.created_at if last_msg else None
        ))
        
    return result

@router.get("/conversations/{conversation_id}", response_model=List[MessageResponse], tags=["Admin - Messages"])
def get_conversation_messages(conversation_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only Admin can use this endpoint")
        
    user_id = current_user["id"]
    
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    if conv.admin_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to access this conversation")
        
    messages = db.query(DBMessage).filter(DBMessage.conversation_id == conversation_id).order_by(DBMessage.created_at.asc()).all()
    return messages

class ReplyRequest(BaseModel):
    message: str

@router.post("/{conversation_id}/reply", response_model=MessageResponse, tags=["Admin - Messages"])
async def admin_reply(conversation_id: int, reply_data: ReplyRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only Admin can use this endpoint")
        
    user_id = current_user["id"]
    role = "admin"
    
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    if conv.admin_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to access this conversation")
        
    sender_id = user_id
    sender_role = "admin"
    receiver_id = conv.field_staff_id
    receiver_role = "staff"
    
    db.query(DBMessage).filter(
        DBMessage.conversation_id == conversation_id,
        DBMessage.receiver_id == user_id,
        DBMessage.receiver_role == role,
        DBMessage.is_read == False
    ).update({"is_read": True})
    db.commit()
    
    new_msg = DBMessage(
        conversation_id=conversation_id,
        sender_id=sender_id,
        sender_role=sender_role,
        receiver_id=receiver_id,
        receiver_role=receiver_role,
        message=reply_data.message,
        is_read=False
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    
    msg_response = MessageResponse.model_validate(new_msg)
    
    await manager.send_to_user(receiver_id, receiver_role, {
        "type": "new_message",
        "message": msg_response.model_dump(mode="json")
    })
    
    receiver_unread_count = get_unread_count_for_user(receiver_id, receiver_role, db)
    await manager.send_to_user(receiver_id, receiver_role, {
        "type": "unread_count",
        "unread_count": receiver_unread_count
    })
    
    await manager.send_to_user(sender_id, sender_role, {
        "type": "new_message",
        "message": msg_response.model_dump(mode="json")
    })

    return msg_response

# --- Messages - Unread Count ---

@router.get("/unread-count", response_model=UnreadCountResponse, tags=["Messages - Unread Count"])
def get_unread_count(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    role = current_user["role"]
    count = get_unread_count_for_user(user_id, role, db)
    return UnreadCountResponse(unread_count=count)

# --- WebSocket ---

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...), db: Session = Depends(get_db)):
    user_info = get_current_user_from_token(token, db)
    if not user_info:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    user_id = user_info["id"]
    role = user_info["role"]
    
    await manager.connect(user_id, role, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                action = payload.get("action")
                
                if action == "mark_read":
                    conv_id_raw = payload.get("conversation_id")
                    if not conv_id_raw:
                        await websocket.send_json({"type": "error", "message": "Missing conversation_id"})
                        continue
                        
                    conversation_id = int(conv_id_raw)
                        
                    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
                    if not conv:
                        await websocket.send_json({"type": "error", "message": "Conversation not found"})
                        continue
                        
                    if role == "admin" and conv.admin_id != user_id:
                        await websocket.send_json({"type": "error", "message": "Unauthorized conversation"})
                        continue
                    elif role == "staff" and conv.field_staff_id != user_id:
                        await websocket.send_json({"type": "error", "message": "Unauthorized conversation"})
                        continue
                        
                    db.query(DBMessage).filter(
                        DBMessage.conversation_id == conversation_id,
                        DBMessage.receiver_id == user_id,
                        DBMessage.receiver_role == role,
                        DBMessage.is_read == False
                    ).update({"is_read": True})
                    db.commit()
                    
                    new_unread_count = get_unread_count_for_user(user_id, role, db)
                    
                    await manager.send_to_user(user_id, role, {
                        "type": "messages_read",
                        "conversation_id": conversation_id,
                        "unread_count": new_unread_count
                    })

                elif action == "send_message":
                    message_text = payload.get("message")
                    
                    if not message_text:
                        await websocket.send_json({"type": "error", "message": "Missing message"})
                        continue
                        
                    if role == "admin":
                        receiver_id = payload.get("receiver_id")
                        if not receiver_id:
                            await websocket.send_json({"type": "error", "message": "Missing receiver_id"})
                            continue
                            
                        receiver_role = "staff"
                        receiver = db.query(Staff).filter(Staff.id == receiver_id).first()
                        if not receiver:
                            await websocket.send_json({"type": "error", "message": "Receiver not found"})
                            continue
                        admin_id = user_id
                        staff_id = receiver_id
                    else:
                        receiver_role = "admin"
                        receiver = db.query(Admin).first()
                        if not receiver:
                            await websocket.send_json({"type": "error", "message": "Receiver not found"})
                            continue
                        receiver_id = receiver.id
                        admin_id = receiver_id
                        staff_id = user_id

                    conversation = db.query(Conversation).filter(
                        Conversation.admin_id == admin_id,
                        Conversation.field_staff_id == staff_id
                    ).first()
                    
                    if not conversation:
                        conversation = Conversation(admin_id=admin_id, field_staff_id=staff_id)
                        db.add(conversation)
                        db.commit()
                        db.refresh(conversation)
                    else:
                        db.query(DBMessage).filter(
                            DBMessage.conversation_id == conversation.id,
                            DBMessage.receiver_id == user_id,
                            DBMessage.receiver_role == role,
                            DBMessage.is_read == False
                        ).update({"is_read": True})
                        db.commit()
                        
                    new_msg = DBMessage(
                        conversation_id=conversation.id,
                        sender_id=user_id,
                        sender_role=role,
                        receiver_id=receiver_id,
                        receiver_role=receiver_role,
                        message=message_text,
                        is_read=False
                    )
                    db.add(new_msg)
                    db.commit()
                    db.refresh(new_msg)
                    
                    msg_response = MessageResponse.model_validate(new_msg)
                    msg_json = msg_response.model_dump(mode="json")
                    
                    await manager.send_to_user(receiver_id, receiver_role, {
                        "type": "new_message",
                        "message": msg_json
                    })
                    
                    receiver_unread_count = get_unread_count_for_user(receiver_id, receiver_role, db)
                    await manager.send_to_user(receiver_id, receiver_role, {
                        "type": "unread_count",
                        "unread_count": receiver_unread_count
                    })
                    
                    await manager.send_to_user(user_id, role, {
                        "type": "new_message",
                        "message": msg_json
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                
    except WebSocketDisconnect:
        manager.disconnect(user_id, role, websocket)
