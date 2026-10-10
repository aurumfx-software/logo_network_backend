from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database_models import Admin, AdminPasswordResetRequest
from schemas.adminAuth import AdminLogin, AdminLoginResponse
from utils.password import verify_password
from utils.jwt import create_access_token
from utils.password import hash_password
from schemas.adminAuth import (
    AdminVerifyOTPRequest,
    AdminResetPasswordRequest
)
from services.email_service import send_password_reset_otp
from services.password_reset_service import (
    create_password_reset_request,
    verify_otp_and_create_token,
    consume_reset_token
)


router = APIRouter(prefix="/admin-auth", tags=["Admin Authentication"])

@router.post("/login", response_model=AdminLoginResponse)
def admin_login(login_data: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == login_data.email).first()
    
    if not admin or not verify_password(login_data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is not active"
        )
        
    access_token = create_access_token(data={"sub": str(admin.id), "role": admin.role})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": admin
    }


@router.post("/forgot-password")
def forgot_password(db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.is_active == True).first()
    
    import uuid
    # Always generate a fake request ID first to use if the admin doesn't exist
    fake_reset_request_id = str(uuid.uuid4())
    
    # Generic response to prevent email enumeration
    generic_response = {
        "success": True,
        "message": "If an active admin account exists, password reset instructions will be sent to the registered email.",
        "reset_request_id": fake_reset_request_id
    }
    
    if not admin:
        print("[Admin Auth] Forgot password requested but no active admin found. Returning fake ID.")
        return generic_response
        
    otp, real_reset_request_id = create_password_reset_request(db, admin.id)
    
    # Update response with the real ID since the account is valid
    generic_response["reset_request_id"] = real_reset_request_id
    
    print(f"[Admin Auth] Initiating password reset for valid admin: {admin.email}")
    success, result = send_password_reset_otp(admin.email, otp)
    if not success:
        # We don't want to expose Resend errors to the client, just return the generic response
        print(f"[Admin Auth] FAILED to send OTP email to {admin.email}: {result}")
    else:
        print(f"[Admin Auth] OTP email successfully sent to {admin.email}")
        
    return generic_response

@router.post("/verify-reset-otp")
def verify_reset_otp(request: AdminVerifyOTPRequest, db: Session = Depends(get_db)):
    reset_token = verify_otp_and_create_token(db, request.reset_request_id, request.otp)
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP, or maximum attempts exceeded"
        )
        
    return {
        "success": True,
        "message": "OTP verified successfully",
        "reset_token": reset_token,
        "expires_in": 600
    }

@router.post("/reset-password")
def reset_password(request: AdminResetPasswordRequest, db: Session = Depends(get_db)):
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
        
    # Basic password strength check could go here if implemented elsewhere
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
        
    # We need to find the admin by reset token, but our schema doesn't send the email in this step.
    # We must scan or assume we can find the request by token hash.
    # Let's adjust consume_reset_token to take the token and return the admin_id instead.
    # Actually, the user requirement says "Verify the reset token hash, expiry, unused status and associated admin account."
    # Since we need to update the password, we need the admin account.
    # I'll query AdminPasswordResetRequest directly here to find the admin.
    
    from services.password_reset_service import hash_value
    import datetime
    
    token_hash = hash_value(request.reset_token)
    
    reset_request = db.query(AdminPasswordResetRequest).filter(
        AdminPasswordResetRequest.reset_token_hash == token_hash
    ).with_for_update().first()
    
    if not reset_request or reset_request.reset_token_consumed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
        
    # Check expiry
    token_expiry = reset_request.reset_token_expiry
    if token_expiry.tzinfo is None:
        token_expiry = token_expiry.replace(tzinfo=datetime.timezone.utc)
        
    if datetime.datetime.now(datetime.timezone.utc) > token_expiry:
        reset_request.reset_token_consumed = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
        
    admin = db.query(Admin).filter(Admin.id == reset_request.admin_id).first()
    
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin account not found or inactive"
        )
        
    # Mark token as consumed and update password
    reset_request.reset_token_consumed = True
    
    # Invalidate all other reset requests for this admin
    db.query(AdminPasswordResetRequest).filter(
        AdminPasswordResetRequest.admin_id == admin.id,
        AdminPasswordResetRequest.id != reset_request.id
    ).update({"reset_token_consumed": True, "otp_consumed": True})
    
    admin.password_hash = hash_password(request.new_password)
    db.commit()
    
    return {
        "success": True,
        "message": "Password reset successfully"
    }
