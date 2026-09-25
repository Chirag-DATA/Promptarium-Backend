import os
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def generate_otp() -> str:
    """Generate a random 6-digit numeric OTP."""
    return f"{random.randint(100000, 999999)}"


def send_otp_email(recipient_email: str, otp: str):
    """Sends a styled confirmation OTP to the recipient for signup."""
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[DEV MODE] SMTP not configured. Signup OTP for {recipient_email}: {otp}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your Promptarium Verification Code: {otp}"
    msg["From"] = f"Promptarium <{SMTP_USER}>"
    msg["To"] = recipient_email

    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 16px; background-color: #ffffff;">
        <h2 style="color: #0f172a; margin-top: 0;">Confirm Your Account</h2>
        <p style="color: #64748b; font-size: 14px; line-height: 1.5;">
            Welcome to Promptarium. Use the 6-digit code below to confirm your email and activate your account.
        </p>
        <div style="text-align: center; margin: 32px 0;">
            <span style="display: inline-block; font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #2563eb; background-color: #eff6ff; padding: 12px 28px; border-radius: 12px; border: 1px solid #bfdbfe;">
                {otp}
            </span>
        </div>
        <p style="color: #94a3b8; font-size: 12px; text-align: center;">
            This verification code expires in 10 minutes. If you did not sign up for Promptarium, you can safely ignore this email.
        </p>
    </div>
    """

    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def send_delete_account_otp_email(recipient_email: str, otp: str):
    """Sends an urgent account deletion confirmation OTP."""
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[DEV MODE] SMTP not configured. Account Deletion OTP for {recipient_email}: {otp}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Action Required: Confirm Account Deletion Code {otp}"
    msg["From"] = f"Promptarium Security <{SMTP_USER}>"
    msg["To"] = recipient_email

    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px; border: 1px solid #fecdd3; border-radius: 16px; background-color: #fff1f2;">
        <h2 style="color: #9f1239; margin-top: 0;">Permanently Delete Account</h2>
        <p style="color: #881337; font-size: 14px; line-height: 1.5;">
            A request was made to permanently delete your Promptarium account and all associated prompts.
        </p>
        <p style="color: #881337; font-size: 14px; line-height: 1.5;">
            <strong>Warning:</strong> This action cannot be undone. All your saved prompts, tags, and profile data will be permanently wiped.
        </p>
        <div style="text-align: center; margin: 28px 0;">
            <span style="display: inline-block; font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #e11d48; background-color: #ffffff; padding: 12px 28px; border-radius: 12px; border: 1px solid #fda4af;">
                {otp}
            </span>
        </div>
        <p style="color: #9f1239; font-size: 12px; text-align: center;">
            This code expires in 10 minutes. If you did NOT request this, change your password immediately.
        </p>
    </div>
    """

    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)