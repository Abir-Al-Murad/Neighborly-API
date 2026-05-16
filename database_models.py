from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text,
    Date, DateTime, Enum, ForeignKey, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
import enum


# ───────────────────────────────────────────────
# Enums
# ───────────────────────────────────────────────

class BloodGroup(str, enum.Enum):
    A_pos = "A+"
    A_neg = "A-"
    B_pos = "B+"
    B_neg = "B-"
    O_pos = "O+"
    O_neg = "O-"
    AB_pos = "AB+"
    AB_neg = "AB-"
    


class ListingType(str, enum.Enum):
    flat_sale = "flat_sale"
    sublet = "sublet"
    monthly_rental = "monthly_rental"
    short_stay = "short_stay"

class SOSStatus(str, enum.Enum):
    active = "active"
    resolved = "resolved"
    false_alarm = "false_alarm"

class SOSNotificationType(str, enum.Enum):
    volunteer = "volunteer"
    general_user = "general_user"

class SOSResponseStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    ignored = "ignored"

class MedicineCondition(str, enum.Enum):
    unopened = "unopened"
    partially_used = "partially_used"

class MedicineStatus(str, enum.Enum):
    available = "available"
    claimed = "claimed"
    expired = "expired"

class MedicineRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class LostFoundType(str, enum.Enum):
    lost = "lost"
    found = "found"

class LostFoundStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"


def enum_type(enum_cls):
    return Enum(enum_cls, values_callable=lambda enum_values: [member.value for member in enum_values])


# ───────────────────────────────────────────────
# Users & Auth
# ───────────────────────────────────────────────

class UserModel(Base):

    __tablename__ = "user"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    lat = Column(Float)
    lng = Column(Float)
    address = Column(Text)
    is_verified = Column(Boolean, default=False)    # True after OTP confirmed
    is_volunteer = Column(Boolean, default=False)
    volunteer_available = Column(Boolean, default=False)
    availability_hours = Column(String)         # e.g. "09:00-22:00"
    sos_false_alarm_count = Column(Integer, default=0)
    last_sos_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    otps = relationship("OTPModel", back_populates="user")
    blood_donor = relationship("BloodDonorModel", back_populates="user", uselist=False)
    sos_events = relationship("SOSEventModel", back_populates="user")
    home_listings = relationship("HomeListingModel", back_populates="user")
    medicine_posts = relationship("MedicinePostModel", back_populates="user")
    medicine_requests = relationship("MedicineRequestModel", back_populates="requester")
    lost_found_posts = relationship("LostFoundPostModel", back_populates="user")
    hazard_alerts = relationship("HazardAlertModel", back_populates="user")
    hazard_confirmations = relationship("HazardConfirmationModel", back_populates="user")
    sos_notifications = relationship("SOSNotificationModel", back_populates="notified_user")


# ───────────────────────────────────────────────
# OTP
# ───────────────────────────────────────────────

class OTPModel(Base):

    __tablename__ = "otp"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("UserModel", back_populates="otps")


# ───────────────────────────────────────────────
# Blood Donors
# ───────────────────────────────────────────────

class BloodDonorModel(Base):

    __tablename__ = "blood_donor"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), unique=True)
    blood_group = Column(enum_type(BloodGroup), index=True)
    last_donation_date = Column(Date)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    lat = Column(Float)
    lng = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("UserModel", back_populates="blood_donor")


# ───────────────────────────────────────────────
# SOS
# ───────────────────────────────────────────────

class SOSEventModel(Base):

    __tablename__ = "sos_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    message = Column(Text)
    voice_url = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    share_live_location = Column(Boolean, default=False)
    status = Column(enum_type(SOSStatus), default=SOSStatus.active)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("UserModel", back_populates="sos_events")
    notifications = relationship("SOSNotificationModel", back_populates="sos_event")


class SOSNotificationModel(Base):

    __tablename__ = "sos_notification"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    sos_id = Column(UUID(as_uuid=True), ForeignKey("sos_event.id"))
    notified_user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    type = Column(enum_type(SOSNotificationType))
    response_status = Column(enum_type(SOSResponseStatus), default=SOSResponseStatus.pending)
    responded_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    sos_event = relationship("SOSEventModel", back_populates="notifications")
    notified_user = relationship("UserModel", back_populates="sos_notifications")


# ───────────────────────────────────────────────
# Home Listings
# ───────────────────────────────────────────────

class HomeListingModel(Base):

    __tablename__ = "home_listing"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    listing_type = Column(enum_type(ListingType))
    title = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float)
    price_unit = Column(String)                 # "per month", "total", etc.
    bedrooms = Column(Integer)
    area_sqft = Column(Float)
    lat = Column(Float)
    lng = Column(Float)
    area_name = Column(String)
    available_from = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("UserModel", back_populates="home_listings")
    photos = relationship("HomePhotoModel", back_populates="listing")


class HomePhotoModel(Base):

    __tablename__ = "home_photo"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("home_listing.id"))
    photo_url = Column(String, nullable=False)
    sort_order = Column(Integer, default=0)

    listing = relationship("HomeListingModel", back_populates="photos")


# ───────────────────────────────────────────────
# Medicine Exchange
# ───────────────────────────────────────────────

class MedicinePostModel(Base):

    __tablename__ = "medicine_post"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    medicine_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    quantity_unit = Column(String)              # "tablets", "strips", "ml", etc.
    expiry_date = Column(Date, nullable=False, index=True)
    condition = Column(enum_type(MedicineCondition))
    pickup_area = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    status = Column(enum_type(MedicineStatus), default=MedicineStatus.available)
    photo_url = Column(String)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("UserModel", back_populates="medicine_posts")
    requests = relationship("MedicineRequestModel", back_populates="medicine")


class MedicineRequestModel(Base):

    __tablename__ = "medicine_request"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    medicine_id = Column(UUID(as_uuid=True), ForeignKey("medicine_post.id"))
    requester_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    status = Column(enum_type(MedicineRequestStatus), default=MedicineRequestStatus.pending)
    created_at = Column(DateTime, server_default=func.now())

    medicine = relationship("MedicinePostModel", back_populates="requests")
    requester = relationship("UserModel", back_populates="medicine_requests")


# ───────────────────────────────────────────────
# Lost & Found
# ───────────────────────────────────────────────

class LostFoundPostModel(Base):

    __tablename__ = "lost_found_post"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    type = Column(enum_type(LostFoundType))          # lost or found
    category = Column(String)                   # id_card, phone, animal, wallet, etc.
    title = Column(String, nullable=False)
    description = Column(Text)
    lat = Column(Float)
    lng = Column(Float)
    area_name = Column(String)
    photo_url = Column(String)
    status = Column(enum_type(LostFoundStatus), default=LostFoundStatus.open)
    lost_found_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("UserModel", back_populates="lost_found_posts")


# ───────────────────────────────────────────────
# Hazard Alerts
# ───────────────────────────────────────────────

class HazardAlertModel(Base):

    __tablename__ = "hazard_alert"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    category = Column(String)                   # pothole, wire, flood, fire, etc.
    description = Column(Text)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    area_name = Column(String)
    confirm_count = Column(Integer, default=0)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("UserModel", back_populates="hazard_alerts")
    confirmations = relationship("HazardConfirmationModel", back_populates="hazard")


class HazardConfirmationModel(Base):

    __tablename__ = "hazard_confirmation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    hazard_id = Column(UUID(as_uuid=True), ForeignKey("hazard_alert.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"))
    created_at = Column(DateTime, server_default=func.now())

    hazard = relationship("HazardAlertModel", back_populates="confirmations")
    user = relationship("UserModel", back_populates="hazard_confirmations")