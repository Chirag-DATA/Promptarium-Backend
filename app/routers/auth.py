from datetime import datetime, timedelta, timezone
import os
import uuid
from sqlalchemy import text

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.email import (
    generate_otp,
    send_delete_account_otp_email,
    send_otp_email,
)
from app.core.rate_limiter import RateLimiter
from app.database import get_session
from app.models.prompt import Prompt
from app.models.user import User
from app.schemas.user import (
    DeleteAccountConfirmRequest,
    ResendOTPRequest,
    Token,
    UserCreate,
    UserRead,
    UserUpdate,
    VerifyOTPRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

UPLOAD_DIR = "app/static/uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
REFRESH_COOKIE_NAME = "promptarium_refresh_token"
OTP_EXPIRE_MINUTES = 10

IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"

login_limiter = RateLimiter(max_requests=5, window_seconds=60)
signup_limiter = RateLimiter(max_requests=5, window_seconds=3600)
delete_limiter = RateLimiter(max_requests=3, window_seconds=300)


def set_refresh_cookie(response: Response, user_id: int):
    refresh_token = create_refresh_token(data={"sub": str(user_id)})
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="none" if IS_PRODUCTION else "lax",
        path="/auth",
        max_age=60 * 60 * 24 * 7,
    )


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(signup_limiter)],
)
def signup(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    existing_user = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()

    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists.",
            )

        otp = generate_otp()
        existing_user.otp_code = otp
        existing_user.otp_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=OTP_EXPIRE_MINUTES
        )
        existing_user.hashed_password = hash_password(user_data.password)
        session.add(existing_user)
        session.commit()

        background_tasks.add_task(send_otp_email, existing_user.email, otp)
        return {"message": "Verification code re-sent. Please check your email."}

    otp = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)

    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        is_verified=False,
        otp_code=otp,
        otp_expires_at=expires_at,
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    background_tasks.add_task(send_otp_email, new_user.email, otp)
    return {"message": "Verification code sent to your email."}


@router.post("/verify-otp", response_model=Token)
def verify_otp(
    data: VerifyOTPRequest,
    response: Response,
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == data.email)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already verified. Please sign in.",
        )

    now = datetime.now(timezone.utc)
    if not user.otp_expires_at or user.otp_expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new one.",
        )

    if user.otp_code != data.otp.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code.",
        )

    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    session.add(user)
    session.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    set_refresh_cookie(response, user.id)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/resend-otp")
def resend_otp(
    data: ResendOTPRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user or user.is_verified:
        return {"message": "If an unverified account exists, a new code has been sent."}

    otp = generate_otp()
    user.otp_code = otp
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)
    session.add(user)
    session.commit()

    background_tasks.add_task(send_otp_email, user.email, otp)
    return {"message": "A fresh verification code has been sent."}


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(login_limiter)],
)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account unverified. Please verify your email OTP before logging in.",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    set_refresh_cookie(response, user.id)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
def refresh_access_token(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found. Please log in again.",
        )

    try:
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token. Please log in again.",
        )

    user = session.get(User, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account unverified.",
        )

    new_access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/auth",
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="none" if IS_PRODUCTION else "lax",
    )
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserRead)
def update_profile(
    updates: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if updates.username:
        existing = session.exec(
            select(User).where(User.username == updates.username)
        ).first()
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That username is already taken.",
            )
        current_user.username = updates.username

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return current_user


@router.post("/me/photo", response_model=UserRead)
def upload_profile_photo(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, JPEG, PNG, or WEBP images are allowed.",
        )

    contents = file.file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must be smaller than 5MB.",
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    current_user.profile_image_url = f"/uploads/{unique_filename}"

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return current_user


# --- NEW: Delete Account OTP Endpoints ---

@router.post(
    "/delete-account/request-otp",
    dependencies=[Depends(delete_limiter)],
)
def request_delete_account_otp(
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    otp = generate_otp()
    current_user.otp_code = otp
    current_user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)
    session.add(current_user)
    session.commit()

    background_tasks.add_task(send_delete_account_otp_email, current_user.email, otp)
    return {"message": "Account deletion verification code sent to your email."}


@router.post("/delete-account/confirm")
def confirm_delete_account(
    data: DeleteAccountConfirmRequest,
    response: Response,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    if not current_user.otp_expires_at or current_user.otp_expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deletion code has expired. Please request a new code.",
        )

    if current_user.otp_code != data.otp.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid deletion verification code.",
        )

    # 1. Delete all likes referencing this user or this user's prompts
    #    (Prevents ForeignKeyViolation on promptlike table)
    session.execute(
        text("""
            DELETE FROM promptlike 
            WHERE user_id = :uid 
               OR prompt_id IN (SELECT id FROM prompt WHERE owner_id = :uid)
        """),
        {"uid": current_user.id},
    )

    # 2. Delete all prompts owned by this user
    user_prompts = session.exec(
        select(Prompt).where(Prompt.owner_id == current_user.id)
    ).all()
    for prompt in user_prompts:
        session.delete(prompt)

    # 3. Remove profile photo from disk if present
    if current_user.profile_image_url and current_user.profile_image_url.startswith("/uploads/"):
        filename = os.path.basename(current_user.profile_image_url)
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    # 4. Permanently remove the user record
    session.delete(current_user)
    session.commit()

    # 5. Invalidate refresh token cookie
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/auth",
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="none" if IS_PRODUCTION else "lax",
    )

    return {"message": "Account and all associated prompts permanently deleted."}