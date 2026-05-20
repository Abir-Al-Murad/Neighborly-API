import os
import random
import string
from datetime import datetime, timedelta
from uuid import UUID

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from twilio.rest import Client as TwilioClient

from database import get_db
from database_models import UserModel as User, OTPModel as OTP
from schemas import (
    UserCreateModel, UserModel,
    OTPRequestModel, OTPVerifyModel,
    LoginModel, TokenModel,
)
import bcrypt

load_dotenv()

# ── Config ────────────────────────────────────────────────
JWT_SECRET      = os.getenv("JWT_SECRET_KEY", "changeme")
JWT_ALGORITHM   = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MIN  = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # 7 days

TWILIO_SID      = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN    = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE    = os.getenv("TWILIO_PHONE_NUMBER")

twilio_client   = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
bearer_scheme   = HTTPBearer()

OTP_EXPIRE_MINUTES = 10


# ── Helpers ───────────────────────────────────────────────

def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def send_otp_sms(phone: str, otp: str):
    try:
        twilio_client.messages.create(
            body=f"Your Neighborly verification code is: {otp}. Valid for {OTP_EXPIRE_MINUTES} minutes.",
            from_=TWILIO_PHONE,
            to=phone,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")



def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.strip().encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        password.strip().encode("utf-8"),
        hashed.strip().encode("utf-8")
    )


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MIN)
    return jwt.encode({"sub": user_id, "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> str:
    """Returns user_id string or raises 401."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")


# ── Auth dependency — use this on every protected route ───

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_token(credentials.credentials)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ── Router ────────────────────────────────────────────────

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


# Step 1 — Register: save user, send OTP
@auth_router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(body: UserCreateModel, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        (User.email == body.email) | (User.phone == body.phone)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email or phone already registered")

    user = User(
        name=body.name,
        phone=body.phone,
        email=body.email,
        password_hash=hash_password(body.password),
        address=body.address,
        lat=body.lat,
        lng=body.lng,
        is_verified=True,         # not verified until OTP confirmed
    )
    db.add(user)
    # db.flush()                     # get user.id without full commit
    db.commit()
    # otp_code = generate_otp()
    # expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)

    # otp = OTP(
    #     user_id=user.id,
    #     code=otp_code,
    #     expires_at=expires_at,
    #     is_used=False,
    # )
    # db.add(otp)
    # db.commit()

    # send_otp_sms(body.phone, otp_code)

    # return {
    #     "message": "OTP sent to your phone number. Verify to complete registration.",
    #     "user_id": str(user.id),
    # }
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}


# Step 2 — Verify OTP: mark user verified, return token
@auth_router.post("/verify-otp", response_model=TokenModel)
def verify_otp(body: OTPVerifyModel, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = (
        db.query(OTP)
        .filter(
            OTP.user_id == body.user_id,
            OTP.code == body.code,
            OTP.is_used == False,
            OTP.expires_at >= datetime.utcnow(),
        )
        .order_by(OTP.expires_at.desc())
        .first()
    )

    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    otp.is_used = True  # type: ignore
    user.is_verified = True  # type: ignore
    db.commit()

    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}


# Resend OTP
@auth_router.post("/resend-otp", response_model=dict)
def resend_otp(body: OTPRequestModel, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == body.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="Phone number not registered")
    if user.is_verified:  # type: ignore
        raise HTTPException(status_code=400, detail="Phone already verified")

    # invalidate old OTPs
    db.query(OTP).filter(OTP.user_id == user.id, OTP.is_used == False).update({"is_used": True})

    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)
    otp = OTP(user_id=user.id, code=otp_code, expires_at=expires_at, is_used=False)
    db.add(otp)
    db.commit()

    send_otp_sms(body.phone, otp_code)
    return {"message": "New OTP sent"}


# Login — phone + password → token
@auth_router.post("/login")
def login(body: LoginModel, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.phone == body.phone
    ).first()

    print(user)

    # First check if user exists
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid phone or password"
        )

    verified = verify_password(
        body.password,
        user.password_hash # type: ignore
    )

    print(f"Password verified: {verified}")

    # Check password
    if not verified:
        raise HTTPException(
            status_code=401,
            detail="Invalid phone or password"
        )

    # Check verification
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Phone not verified. Please verify OTP first."
        )

    token = create_access_token(str(user.id))

    return {
        "token": {
            "access_token": token,
            "token_type": "bearer"
        },
        "user": user
    }