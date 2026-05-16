from fastapi import HTTPException
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

from pydantic import BaseModel,EmailStr,field_validator
import phonenumbers

from database_models import (
    BloodGroup, ListingType, SOSStatus, SOSNotificationType, SOSResponseStatus,
    MedicineCondition, MedicineStatus, MedicineRequestStatus,
    LostFoundType, LostFoundStatus
)


# ───────────────────────────────────────────────
# Auth / OTP
# ───────────────────────────────────────────────

class OTPRequestModel(BaseModel):
    phone: str

class OTPVerifyModel(BaseModel):
    user_id: UUID
    code: str

class LoginModel(BaseModel):
    phone: str
    password: str

class TokenModel(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ───────────────────────────────────────────────
# User
# ───────────────────────────────────────────────

class UserCreateModel(BaseModel):
    name: str
    phone: str
    @field_validator("phone")
    @classmethod
    def validate_phone(cls,value):
        try:
            parsed = phonenumbers.parse(value, "BD")
            if not phonenumbers.is_valid_number(parsed):
                raise HTTPException(
                status_code=400,
                detail="Invalid phone number"
            )
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise HTTPException(
                status_code=400,
                detail="Invalid phone number format"
            )
    email: EmailStr
    password: str
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class UserUpdateModel(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    is_volunteer: Optional[bool] = None
    volunteer_available: Optional[bool] = None
    availability_hours: Optional[str] = None


class UserModel(BaseModel):
    id: UUID
    name: str
    phone: Optional[str]
    email: EmailStr
    address: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    is_verified: bool
    is_volunteer: bool
    volunteer_available: bool
    availability_hours: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ───────────────────────────────────────────────
# Blood Donor
# ───────────────────────────────────────────────

class BloodDonorCreateModel(BaseModel):
    blood_group: BloodGroup
    last_donation_date: Optional[date] = None
    notes: Optional[str] = None
    lat: float
    lng: float


class BloodDonorUpdateModel(BaseModel):
    blood_group: Optional[BloodGroup] = None
    last_donation_date: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class BloodDonorModel(BaseModel):
    id: UUID
    user_id: UUID
    blood_group: BloodGroup
    last_donation_date: Optional[date]
    is_active: bool
    notes: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class BloodDonorWithUserModel(BloodDonorModel):
    user: Optional[UserModel] = None

    model_config = ConfigDict(from_attributes=True)


class BloodDonorWithDistanceModel(BaseModel):
    distance_km: float
    donor: BloodDonorWithUserModel

    model_config = ConfigDict(from_attributes=True)


# ───────────────────────────────────────────────
# SOS
# ───────────────────────────────────────────────

class SOSCreateModel(BaseModel):
    message: Optional[str] = None
    voice_url: Optional[str] = None
    lat: float
    lng: float
    share_live_location: Optional[bool] = False


class SOSUpdateModel(BaseModel):
    status: Optional[SOSStatus] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class SOSEventModel(BaseModel):
    id: UUID
    user_id: UUID
    message: Optional[str]
    voice_url: Optional[str]
    lat: float
    lng: float
    share_live_location: bool
    status: SOSStatus
    resolved_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SOSNotificationCreateModel(BaseModel):
    sos_id: UUID
    notified_user_id: UUID
    type: SOSNotificationType


class SOSNotificationRespondModel(BaseModel):
    response_status: SOSResponseStatus


class SOSNotificationModel(BaseModel):
    id: UUID
    sos_id: UUID
    notified_user_id: UUID
    type: SOSNotificationType
    response_status: SOSResponseStatus
    responded_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ───────────────────────────────────────────────
# Home Listing
# ───────────────────────────────────────────────

class HomePhotoModel(BaseModel):
    id: UUID
    listing_id: UUID
    photo_url: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class HomeListingCreateModel(BaseModel):
    listing_type: ListingType
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    price_unit: Optional[str] = None
    bedrooms: Optional[int] = None
    area_sqft: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    area_name: Optional[str] = None
    available_from: Optional[date] = None


class HomeListingUpdateModel(BaseModel):
    listing_type: Optional[ListingType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    price_unit: Optional[str] = None
    bedrooms: Optional[int] = None
    area_sqft: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    area_name: Optional[str] = None
    available_from: Optional[date] = None
    is_active: Optional[bool] = None


class HomeListingModel(BaseModel):
    id: UUID
    user_id: UUID
    listing_type: ListingType
    title: str
    description: Optional[str]
    price: Optional[float]
    price_unit: Optional[str]
    bedrooms: Optional[int]
    area_sqft: Optional[float]
    lat: Optional[float]
    lng: Optional[float]
    area_name: Optional[str]
    available_from: Optional[date]
    is_active: bool
    created_at: datetime
    photos: List[HomePhotoModel] = []

    model_config = ConfigDict(from_attributes=True)


# ───────────────────────────────────────────────
# Medicine Exchange
# ───────────────────────────────────────────────

class MedicinePostCreateModel(BaseModel):
    medicine_name: str
    quantity: int
    quantity_unit: Optional[str] = None
    expiry_date: date
    condition: MedicineCondition
    pickup_area: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    photo_url: Optional[str] = None


class MedicinePostUpdateModel(BaseModel):
    medicine_name: Optional[str] = None
    quantity: Optional[int] = None
    quantity_unit: Optional[str] = None
    expiry_date: Optional[date] = None
    condition: Optional[MedicineCondition] = None
    pickup_area: Optional[str] = None
    status: Optional[MedicineStatus] = None
    photo_url: Optional[str] = None


class MedicinePostModel(BaseModel):
    id: UUID
    user_id: UUID
    medicine_name: str
    quantity: int
    quantity_unit: Optional[str]
    expiry_date: date
    condition: MedicineCondition
    pickup_area: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    status: MedicineStatus
    photo_url: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicineRequestCreateModel(BaseModel):
    medicine_id: UUID


class MedicineRequestUpdateModel(BaseModel):
    status: MedicineRequestStatus


class MedicineRequestModel(BaseModel):
    id: UUID
    medicine_id: UUID
    requester_id: UUID
    status: MedicineRequestStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ───────────────────────────────────────────────
# Lost & Found
# ───────────────────────────────────────────────

class LostFoundPostCreateModel(BaseModel):
    type: LostFoundType
    category: str
    title: str
    description: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    area_name: Optional[str] = None
    photo_url: Optional[str] = None
    lost_found_date: Optional[date] = None


class LostFoundPostUpdateModel(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    area_name: Optional[str] = None
    photo_url: Optional[str] = None
    status: Optional[LostFoundStatus] = None


class LostFoundPostModel(BaseModel):
    id: UUID
    user_id: UUID
    type: LostFoundType
    category: str
    title: str
    description: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    area_name: Optional[str]
    photo_url: Optional[str]
    status: LostFoundStatus
    lost_found_date: Optional[date]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ───────────────────────────────────────────────
# Hazard Alert
# ───────────────────────────────────────────────

class HazardAlertCreateModel(BaseModel):
    category: str
    description: Optional[str] = None
    lat: float
    lng: float
    area_name: Optional[str] = None


class HazardAlertUpdateModel(BaseModel):
    description: Optional[str] = None
    is_resolved: Optional[bool] = None


class HazardAlertModel(BaseModel):
    id: UUID
    user_id: UUID
    category: str
    description: Optional[str]
    lat: float
    lng: float
    area_name: Optional[str]
    confirm_count: int
    is_resolved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HazardConfirmationModel(BaseModel):
    id: UUID
    hazard_id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)