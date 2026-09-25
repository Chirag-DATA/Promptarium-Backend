import json
import os
import random
import smtplib
import urllib.error
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Brevo HTTP API Configuration (for Render on Port 443)
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or os.getenv("SMTP_USER")

# Fallback SMTP Configuration (for local development on Port 587)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def generate_otp() -> str:
    """Generate a random 6-digit numeric OTP."""
    return f"{random.randint(100000, 999999)}"


def _send_via_brevo_api(recipient_email: str, subject: str, html_content: str):
    """Sends an email via Brevo REST API over standard HTTPS (Port 443)."""
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }
    payload = {
        "sender": {"name": "Promptarium", "email": SENDER_EMAIL},
        "to": [{"email": recipient_email}],
        "subject": subject,
        "htmlContent": html_content,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"[EMAIL SUCCESS] Brevo API delivered email to {recipient_email}. Status: {response.status}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"[EMAIL ERROR] Brevo API failed ({e.code}): {error_body}")
    except Exception as e:
        print(f"[EMAIL ERROR] Unexpected error sending via Brevo API: {e}")


def _send_via_smtp(recipient_email: str, subject: str, html_content: str):
    """Sends an email via standard SMTP (local development only)."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Promptarium <{SMTP_USER}>"
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[EMAIL SUCCESS] SMTP delivered email to {recipient_email}")
    except Exception as e:
        print(f"[EMAIL ERROR] SMTP delivery failed: {e}")


def send_otp_email(recipient_email: str, otp: str):
    """Dispatches signup verification OTP."""
    subject = f"Your Promptarium Verification Code: {otp}"
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

    if BREVO_API_KEY and SENDER_EMAIL:
        _send_via_brevo_api(recipient_email, subject, html_content)
    elif SMTP_USER and SMTP_PASSWORD:
        _send_via_smtp(recipient_email, subject, html_content)
    else:
        print(f"[DEV MODE] Email provider not configured. OTP for {recipient_email}: {otp}")


def send_delete_account_otp_email(recipient_email: str, otp: str):
    """Dispatches account deletion verification OTP."""
    subject = f"Action Required: Confirm Account Deletion Code {otp}"
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

    if BREVO_API_KEY and SENDER_EMAIL:
        _send_via_brevo_api(recipient_email, subject, html_content)
    elif SMTP_USER and SMTP_PASSWORD:
        _send_via_smtp(recipient_email, subject, html_content)
    else:
        print(f"[DEV MODE] Email provider not configured. Account Deletion OTP for {recipient_email}: {otp}")