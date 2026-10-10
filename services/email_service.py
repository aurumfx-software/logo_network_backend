import os
import resend
from dotenv import load_dotenv

# load_dotenv()

# resend.api_key = os.getenv("RESEND_API_KEY")
# from_email = os.getenv("RESEND_FROM_EMAIL", "noreply@backend.aurumfx.org")



load_dotenv()

resend_api_key = os.getenv("RESEND_API_KEY")
from_email = os.getenv("RESEND_FROM_EMAIL")

if not resend_api_key:
    print("[Email Service] ERROR: RESEND_API_KEY is missing.")
else:
    resend.api_key = resend_api_key

if not from_email:
    print("[Email Service] ERROR: RESEND_FROM_EMAIL is missing.")







def send_password_reset_otp(to_email: str, otp: str, expiry_minutes: int = 5):
    """
    Send an OTP for password reset via Resend.
    """
    subject = "Admin Password Reset OTP"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
        <h2 style="color: #333; text-align: center;">Password Reset Request</h2>
        <p style="color: #555; font-size: 16px;">Hello,</p>
        <p style="color: #555; font-size: 16px;">We received a request to reset your admin password. Your One-Time Password (OTP) is:</p>
        <div style="text-align: center; margin: 30px 0;">
            <span style="font-size: 32px; font-weight: bold; background-color: #f4f4f4; padding: 10px 20px; border-radius: 5px; letter-spacing: 5px; color: #333;">{otp}</span>
        </div>
        <p style="color: #555; font-size: 16px;">This OTP will expire in <strong>{expiry_minutes} minutes</strong>.</p>
        <p style="color: #d9534f; font-size: 14px; font-weight: bold;">Do not share this OTP with anyone. If you did not request a password reset, please ignore this email.</p>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px; text-align: center;">This is an automated message, please do not reply.</p>
    </div>
    """
    
    try:
        params = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        email = resend.Emails.send(params)
        print(f"[Email Service] Resend successfully accepted the OTP email request for {to_email}. Response: {email}")
        return True, email
    except Exception as e:
        print(f"[Email Service] CRITICAL ERROR sending email via Resend to {to_email}: {str(e)}")
        # If it's a resend-specific error, the exception string usually contains the API response
        return False, str(e)
