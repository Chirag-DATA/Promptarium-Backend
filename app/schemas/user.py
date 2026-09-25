from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    username: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_verified: bool
    created_at: datetime


class UserUpdate(BaseModel):
    username: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ResendOTPRequest(BaseModel):
    email: EmailStr


class DeleteAccountConfirmRequest(BaseModel):
    otp: str