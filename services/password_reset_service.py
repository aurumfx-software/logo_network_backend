import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from database_models import AdminPasswordResetRequest
import hashlib

def generate_otp(length=6) -> str:
    """Generate a cryptographically secure random numeric OTP."""
    digits = string.digits
    return ''.join(secrets.choice(digits) for _ in range(length))

def hash_value(value: str) -> str:
    """Create a SHA-256 hash of a string value."""
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def create_password_reset_request(db: Session, admin_id: int) -> tuple[str, str, str]:
    """
    Creates a new password reset request with an OTP.
    Returns (otp, reset_request_id).
    """
    # Invalidate previous unconsumed requests for this admin
    db.query(AdminPasswordResetRequest).filter(
        AdminPasswordResetRequest.admin_id == admin_id,
        AdminPasswordResetRequest.otp_consumed == False
    ).update({"otp_consumed": True})
    
    otp = generate_otp()
    otp_hash = hash_value(otp)
    reset_request_id = str(uuid.uuid4())
    
    # Expiry 5 minutes
    expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    reset_request = AdminPasswordResetRequest(
        admin_id=admin_id,
        reset_request_id=reset_request_id,
        otp_hash=otp_hash,
        otp_expiry=expiry
    )
    db.add(reset_request)
    db.commit()
    db.refresh(reset_request)
    
    return otp, reset_request_id

def verify_otp_and_create_token(db: Session, reset_request_id: str, otp: str) -> str | None:
    """
    Verifies the OTP and returns a reset token if successful.
    Returns None if validation fails.
    """
    reset_request = db.query(AdminPasswordResetRequest).filter(
        AdminPasswordResetRequest.reset_request_id == reset_request_id
    ).with_for_update().first() # Lock the row to prevent race conditions
    
    if not reset_request:
        print(f"[Password Reset] Verification failed: reset_request_id {reset_request_id} not found")
        return None
        
    if reset_request.otp_consumed:
        print(f"[Password Reset] Verification failed: OTP already consumed for reset_request_id {reset_request_id}")
        return None
        
    # Check expiry properly
    otp_expiry = reset_request.otp_expiry
    if otp_expiry.tzinfo is None:
        otp_expiry = otp_expiry.replace(tzinfo=timezone.utc)
        
    if datetime.now(timezone.utc) > otp_expiry:
        print(f"[Password Reset] Verification failed: OTP expired for reset_request_id {reset_request_id}")
        reset_request.otp_consumed = True
        db.commit()
        return None
        
    # Check attempts
    if reset_request.otp_attempts >= 5:
        print(f"[Password Reset] Verification failed: Maximum attempts exceeded for reset_request_id {reset_request_id}")
        reset_request.otp_consumed = True
        db.commit()
        return None
        
    # Increment attempts
    reset_request.otp_attempts += 1
    
    # Verify hash
    if reset_request.otp_hash != hash_value(otp):
        print(f"[Password Reset] Verification failed: Invalid OTP hash for reset_request_id {reset_request_id}")
        # If it reached 5 attempts after this increment, mark consumed
        if reset_request.otp_attempts >= 5:
            reset_request.otp_consumed = True
        db.commit()
        return None
        
    # Valid OTP
    print(f"[Password Reset] OTP successfully verified for reset_request_id {reset_request_id}")
    reset_request.otp_consumed = True
    
    # Generate reset token
    reset_token = str(uuid.uuid4())
    reset_request.reset_token_hash = hash_value(reset_token)
    reset_request.reset_token_expiry = datetime.now(timezone.utc) + timedelta(minutes=10) # Token valid for 10 min
    
    db.commit()
    return reset_token

def consume_reset_token(db: Session, admin_id: int, reset_token: str) -> bool:
    """
    Verifies and consumes a reset token.
    Returns True if valid and consumed, False otherwise.
    """
    token_hash = hash_value(reset_token)
    
    reset_request = db.query(AdminPasswordResetRequest).filter(
        AdminPasswordResetRequest.admin_id == admin_id,
        AdminPasswordResetRequest.reset_token_hash == token_hash
    ).with_for_update().first()
    
    if not reset_request:
        return False
        
    if reset_request.reset_token_consumed:
        return False
        
    # Check expiry properly
    token_expiry = reset_request.reset_token_expiry
    if token_expiry.tzinfo is None:
        token_expiry = token_expiry.replace(tzinfo=timezone.utc)
        
    if datetime.now(timezone.utc) > token_expiry:
        print(f"[Password Reset] Token consumption failed: Token expired for reset_request_id {reset_request.reset_request_id}")
        reset_request.reset_token_consumed = True
        db.commit()
        return False
        
    # Mark token as consumed
    reset_request.reset_token_consumed = True
    
    # Invalidate all other reset requests for this admin to be safe
    db.query(AdminPasswordResetRequest).filter(
        AdminPasswordResetRequest.admin_id == admin_id,
        AdminPasswordResetRequest.id != reset_request.id
    ).update({"reset_token_consumed": True, "otp_consumed": True})
    
    # The password update will be committed in the router
    return True
