# from math import radians, cos, sin, asin, sqrt
# from uuid import UUID
# from datetime import datetime, date, timedelta
# from typing import List, Optional

# from fastapi import APIRouter, Depends, HTTPException, Query, status
# from sqlalchemy.orm import Session

# from database import get_db
# from database_models import (
#     BloodGroup,
#     UserModel as User,
#     BloodDonorModel as BloodDonor,
#     SOSEventModel as SOSEvent,
#     SOSNotificationModel as SOSNotification,
#     HomeListingModel as HomeListing,
#     HomePhotoModel as HomePhoto,
#     MedicinePostModel as MedicinePost,
#     MedicineRequestModel as MedicineRequest,
#     LostFoundPostModel as LostFoundPost,
#     HazardAlertModel as HazardAlert,
#     HazardConfirmationModel as HazardConfirmation,
#     SOSStatus, SOSNotificationType, SOSResponseStatus,
#     MedicineStatus, LostFoundStatus
# )
# from schemas import (
#     BloodDonorWithDistanceModel, UserCreateModel, UserUpdateModel, UserModel,
#     BloodDonorCreateModel, BloodDonorUpdateModel, BloodDonorModel, BloodDonorWithUserModel,
#     SOSCreateModel, SOSUpdateModel, SOSEventModel,
#     SOSNotificationModel, SOSNotificationRespondModel,
#     HomeListingCreateModel, HomeListingUpdateModel, HomeListingModel, HomePhotoModel,
#     MedicinePostCreateModel, MedicinePostUpdateModel, MedicinePostModel,
#     MedicineRequestCreateModel, MedicineRequestUpdateModel, MedicineRequestModel,
#     LostFoundPostCreateModel, LostFoundPostUpdateModel, LostFoundPostModel,
#     HazardAlertCreateModel, HazardAlertUpdateModel, HazardAlertModel, HazardConfirmationModel
# )
# from auth import get_current_user
# import bcrypt


# # ───────────────────────────────────────────────
# # Helpers
# # ───────────────────────────────────────────────

# def haversine_km(lat1, lng1, lat2, lng2) -> float:
#     R = 6371
#     lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
#     dlat = lat2 - lat1
#     dlng = lng2 - lng1
#     a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
#     return R * 2 * asin(sqrt(a))

# def get_user_or_404(user_id: UUID, db: Session) -> User:
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user


# # ───────────────────────────────────────────────
# # Users
# # ───────────────────────────────────────────────

# user_router = APIRouter(prefix="/users", tags=["Users"])

# @user_router.get("/me", response_model=UserModel)
# def get_me(current_user: User = Depends(get_current_user)):
#     return current_user

# @user_router.get("/{user_id}", response_model=UserModel)
# def get_user(
#     user_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     return get_user_or_404(user_id, db)


# @user_router.patch("/{user_id}", response_model=UserModel)
# def update_user(
#     user_id: UUID,
#     body: UserUpdateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     if current_user.id != user_id: # type: ignore
#         raise HTTPException(status_code=403, detail="You can only update your own profile")
#     user = get_user_or_404(user_id, db)
#     for field, value in body.model_dump(exclude_none=True).items():
#         setattr(user, field, value)
#     db.commit()
#     db.refresh(user)
#     return user


# @user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_user(
#     user_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     if current_user.id != user_id: # type: ignore
#         raise HTTPException(status_code=403, detail="You can only delete your own account")
#     user = get_user_or_404(user_id, db)
#     db.delete(user)
#     db.commit()


# # ───────────────────────────────────────────────
# # Blood Donors
# # ───────────────────────────────────────────────

# blood_router = APIRouter(prefix="/blood", tags=["Blood Donors"])

# @blood_router.post("/register", response_model=BloodDonorModel, status_code=status.HTTP_201_CREATED)
# def register_donor(
#     body: BloodDonorCreateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     existing = db.query(BloodDonor).filter(BloodDonor.user_id == current_user.id).first()
#     if existing:
#         raise HTTPException(status_code=400, detail="You are already a registered donor")

#     donor = BloodDonor(
#         user_id=current_user.id,
#         blood_group=body.blood_group,
#         last_donation_date=body.last_donation_date,
#         notes=body.notes,
#         lat=body.lat,
#         lng=body.lng,
#     )
#     db.add(donor)
#     db.commit()
#     db.refresh(donor)
#     return donor


# @blood_router.get("/search", response_model=List[BloodDonorWithUserModel])
# def search_donors(
#     blood_group: BloodGroup,
#     lat: float,
#     lng: float,
#     radius_km: float = Query(default=2.0, le=50.0),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     radii = sorted(set(r for r in [radius_km, 5.0, 10.0] if r >= radius_km))
#     donors = db.query(BloodDonor).filter(
#         BloodDonor.blood_group == blood_group,
#         BloodDonor.is_active == True,
#         BloodDonor.lat.isnot(None),
#         BloodDonor.lng.isnot(None),
#     ).all()

#     for radius in radii:
#         nearby = [d for d in donors if haversine_km(lat, lng, d.lat, d.lng) <= radius]
#         if nearby:
#             return nearby
#     return []



# @blood_router.get(
#     "/nearest",
#     response_model=List[BloodDonorWithDistanceModel]
# )
# def get_nearest_donors(
#     lat: float,
#     lng: float,
#     blood_group: Optional[BloodGroup] = None,
#     limit: int = Query(default=10, le=50),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):

#     query = db.query(BloodDonor).filter(
#         BloodDonor.is_active == True,
#         BloodDonor.lat.isnot(None),
#         BloodDonor.lng.isnot(None),
#     )

#     if blood_group is not None:
#         query = query.filter(BloodDonor.blood_group == blood_group)

#     donors = query.all()

#     donors_with_distance = sorted(
#         [
#             {
#                 "distance_km": round(
#                     haversine_km(lat, lng, donor.lat, donor.lng),
#                     2
#                 ),
#                 "donor": donor
#             }
#             for donor in donors
#         ],
#         key=lambda x: x["distance_km"]
#     )

#     return donors_with_distance[:limit]

# @blood_router.get("/{donor_id}", response_model=BloodDonorWithUserModel)
# def get_donor(
#     donor_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     donor = db.query(BloodDonor).filter(BloodDonor.id == donor_id).first()
#     if not donor:
#         raise HTTPException(status_code=404, detail="Donor not found")
#     return donor


# @blood_router.patch("/{donor_id}", response_model=BloodDonorModel)
# def update_donor(
#     donor_id: UUID,
#     body: BloodDonorUpdateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     donor = db.query(BloodDonor).filter(BloodDonor.id == donor_id).first()
#     if not donor:
#         raise HTTPException(status_code=404, detail="Donor not found")
#     if donor.user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your donor profile")
#     for field, value in body.model_dump(exclude_none=True).items():
#         setattr(donor, field, value)
#     db.commit()
#     db.refresh(donor)
#     return donor


# @blood_router.delete("/{donor_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_donor(
#     donor_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     donor = db.query(BloodDonor).filter(BloodDonor.id == donor_id).first()
#     if not donor:
#         raise HTTPException(status_code=404, detail="Donor not found")
#     if donor.user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your donor profile")
#     db.delete(donor)
#     db.commit()


# # ───────────────────────────────────────────────
# # SOS
# # ───────────────────────────────────────────────

# sos_router = APIRouter(prefix="/sos", tags=["SOS"])

# SOS_VOLUNTEER_RADIUS_KM  = 2.0
# SOS_VOLUNTEER_EXPAND_KM  = [5.0, 10.0]
# SOS_COOLDOWN_MINUTES     = 30
# SOS_MAX_VOLUNTEERS_PINGED = 3

# def notify_nearby_volunteers(sos: SOSEvent, db: Session):
#     radii = [SOS_VOLUNTEER_RADIUS_KM] + SOS_VOLUNTEER_EXPAND_KM
#     cooldown_cutoff = datetime.utcnow() - timedelta(minutes=SOS_COOLDOWN_MINUTES)

#     volunteers = db.query(User).filter(
#         User.is_volunteer == True,
#         User.volunteer_available == True,
#         User.lat.isnot(None),
#         User.lng.isnot(None),
#         User.id != sos.user_id,
#         (User.last_sos_at == None) | (User.last_sos_at < cooldown_cutoff)
#     ).all()

#     selected = []
#     for radius in radii:
#         nearby = [v for v in volunteers if haversine_km(sos.lat, sos.lng, v.lat, v.lng) <= radius]
#         nearby.sort(key=lambda v: v.last_sos_at or datetime.min)
#         selected = nearby[:SOS_MAX_VOLUNTEERS_PINGED]
#         if selected:
#             break

#     for volunteer in selected:
#         notif = SOSNotification(
#             sos_id=sos.id,
#             notified_user_id=volunteer.id,
#             type=SOSNotificationType.volunteer,
#             response_status=SOSResponseStatus.pending,
#         )
#         db.add(notif)
#         volunteer.last_sos_at = datetime.utcnow()  # type: ignore

#     db.commit()
#     return selected


# @sos_router.post("", response_model=SOSEventModel, status_code=status.HTTP_201_CREATED)
# def trigger_sos(
#     body: SOSCreateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     if current_user.sos_false_alarm_count >= 3:  # type: ignore
#         raise HTTPException(status_code=403, detail="Account flagged for repeated false SOS alarms")

#     sos = SOSEvent(
#         user_id=current_user.id,
#         message=body.message,
#         voice_url=body.voice_url,
#         lat=body.lat,
#         lng=body.lng,
#         share_live_location=body.share_live_location,
#         status=SOSStatus.active,
#     )
#     db.add(sos)
#     db.commit()
#     db.refresh(sos)
#     notify_nearby_volunteers(sos, db)
#     return sos


# @sos_router.patch("/{sos_id}/resolve", response_model=SOSEventModel)
# def resolve_sos(
#     sos_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     sos = db.query(SOSEvent).filter(SOSEvent.id == sos_id).first()
#     if not sos:
#         raise HTTPException(status_code=404, detail="SOS event not found")
#     if sos.user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your SOS event")
#     sos.status = SOSStatus.resolved  # type: ignore
#     sos.resolved_at = datetime.utcnow()  # type: ignore
#     db.commit()
#     db.refresh(sos)
#     return sos


# @sos_router.patch("/{sos_id}/false-alarm", response_model=SOSEventModel)
# def mark_false_alarm(
#     sos_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     if not current_user.is_volunteer: # type: ignore
#         raise HTTPException(status_code=403, detail="Only volunteers can mark false alarms")
#     sos = db.query(SOSEvent).filter(SOSEvent.id == sos_id).first()
#     if not sos:
#         raise HTTPException(status_code=404, detail="SOS event not found")
#     sos.status = SOSStatus.false_alarm  # type: ignore
#     sos.resolved_at = datetime.utcnow()  # type: ignore
#     user = get_user_or_404(sos.user_id, db)  # type: ignore
#     user.sos_false_alarm_count += 1  # type: ignore
#     db.commit()
#     db.refresh(sos)
#     return sos


# @sos_router.patch("/notifications/{notif_id}/respond", response_model=SOSNotificationModel)
# def respond_to_sos(
#     notif_id: UUID,
#     body: SOSNotificationRespondModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     notif = db.query(SOSNotification).filter(SOSNotification.id == notif_id).first()
#     if not notif:
#         raise HTTPException(status_code=404, detail="Notification not found")
#     if notif.notified_user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your notification")
#     notif.response_status = body.response_status  # type: ignore
#     notif.responded_at = datetime.utcnow()  # type: ignore
#     db.commit()
#     db.refresh(notif)
#     return notif


# @sos_router.patch("/{sos_id}/location", response_model=SOSEventModel)
# def update_sos_location(
#     sos_id: UUID,
#     body: SOSUpdateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     sos = db.query(SOSEvent).filter(SOSEvent.id == sos_id).first()
#     if not sos:
#         raise HTTPException(status_code=404, detail="SOS event not found")
#     if sos.user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your SOS event")
#     if body.lat:
#         sos.lat = body.lat  # type: ignore
#     if body.lng:
#         sos.lng = body.lng  # type: ignore
#     db.commit()
#     db.refresh(sos)
#     return sos


# @sos_router.get("/history", response_model=List[SOSEventModel])
# def get_my_sos_history(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     return db.query(SOSEvent).filter(SOSEvent.user_id == current_user.id).all()


# # ───────────────────────────────────────────────
# # Home Listings
# # ───────────────────────────────────────────────

# home_router = APIRouter(prefix="/home", tags=["Home Listings"])

# @home_router.post("", response_model=HomeListingModel, status_code=status.HTTP_201_CREATED)
# def create_listing(
#     body: HomeListingCreateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     listing = HomeListing(user_id=current_user.id, **body.model_dump())
#     db.add(listing)
#     db.commit()
#     db.refresh(listing)
#     return listing


# @home_router.get("", response_model=List[HomeListingModel])
# def get_listings(
#     lat: Optional[float] = None,
#     lng: Optional[float] = None,
#     radius_km: float = Query(default=2.0, le=50.0),
#     listing_type: Optional[str] = None,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     query = db.query(HomeListing).filter(HomeListing.is_active == True)
#     if listing_type:
#         query = query.filter(HomeListing.listing_type == listing_type)
#     listings = query.all()
#     if lat and lng:
#         listings = [
#             l for l in listings
#             if l.lat is not None and l.lng is not None
#             and haversine_km(lat, lng, l.lat, l.lng) <= radius_km  # type: ignore
#         ]
#     return listings


# @home_router.get("/{listing_id}", response_model=HomeListingModel)
# def get_listing(
#     listing_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     listing = db.query(HomeListing).filter(HomeListing.id == listing_id).first()
#     if not listing:
#         raise HTTPException(status_code=404, detail="Listing not found")
#     return listing


# @home_router.patch("/{listing_id}", response_model=HomeListingModel)
# def update_listing(
#     listing_id: UUID,
#     body: HomeListingUpdateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     listing = db.query(HomeListing).filter(HomeListing.id == listing_id).first()
#     if not listing:
#         raise HTTPException(status_code=404, detail="Listing not found")
#     if listing.user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your listing")
#     for field, value in body.model_dump(exclude_none=True).items():
#         setattr(listing, field, value)
#     db.commit()
#     db.refresh(listing)
#     return listing


# @home_router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_listing(
#     listing_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     listing = db.query(HomeListing).filter(HomeListing.id == listing_id).first()
#     if not listing:
#         raise HTTPException(status_code=404, detail="Listing not found")
#     if listing.user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your listing")
#     db.delete(listing)
#     db.commit()


# @home_router.post("/{listing_id}/photos", response_model=HomePhotoModel, status_code=status.HTTP_201_CREATED)
# def add_photo(
#     listing_id: UUID,
#     photo_url: str,
#     sort_order: int = 0,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     listing = db.query(HomeListing).filter(HomeListing.id == listing_id).first()
#     if not listing:
#         raise HTTPException(status_code=404, detail="Listing not found")
#     if listing.user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your listing")
#     photo = HomePhoto(listing_id=listing_id, photo_url=photo_url, sort_order=sort_order)
#     db.add(photo)
#     db.commit()
#     db.refresh(photo)
#     return photo


# # ───────────────────────────────────────────────
# # Medicine Exchange
# # ───────────────────────────────────────────────

# medicine_router = APIRouter(prefix="/medicine", tags=["Medicine Exchange"])

# @medicine_router.post("", response_model=MedicinePostModel, status_code=status.HTTP_201_CREATED)
# def create_medicine_post(
#     body: MedicinePostCreateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     post = MedicinePost(user_id=current_user.id, **body.model_dump())
#     db.add(post)
#     db.commit()
#     db.refresh(post)
#     return post


# @medicine_router.get("", response_model=List[MedicinePostModel])
# def get_medicine_posts(
#     lat: Optional[float] = None,
#     lng: Optional[float] = None,
#     radius_km: float = Query(default=2.0, le=50.0),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     today = date.today()
#     posts = db.query(MedicinePost).filter(
#         MedicinePost.status == MedicineStatus.available,
#         MedicinePost.expiry_date >= today,
#     ).all()
#     if lat and lng:
#         posts = [
#             p for p in posts
#             if p.lat is not None and p.lng is not None
#             and haversine_km(lat, lng, p.lat, p.lng) <= radius_km  # type: ignore
#         ]
#     return posts


# @medicine_router.get("/{post_id}", response_model=MedicinePostModel)
# def get_medicine_post(
#     post_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     post = db.query(MedicinePost).filter(MedicinePost.id == post_id).first()
#     if not post:
#         raise HTTPException(status_code=404, detail="Medicine post not found")
#     return post


# @medicine_router.patch("/{post_id}", response_model=MedicinePostModel)
# def update_medicine_post(
#     post_id: UUID,
#     body: MedicinePostUpdateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     post = db.query(MedicinePost).filter(MedicinePost.id == post_id).first()
#     if not post:
#         raise HTTPException(status_code=404, detail="Medicine post not found")
#     if post.user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your post")
#     for field, value in body.model_dump(exclude_none=True).items():
#         setattr(post, field, value)
#     db.commit()
#     db.refresh(post)
#     return post


# @medicine_router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_medicine_post(
#     post_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     post = db.query(MedicinePost).filter(MedicinePost.id == post_id).first()
#     if not post:
#         raise HTTPException(status_code=404, detail="Medicine post not found")
#     if post.user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your post")
#     db.delete(post)
#     db.commit()


# @medicine_router.post("/{post_id}/request", response_model=MedicineRequestModel, status_code=status.HTTP_201_CREATED)
# def request_medicine(
#     post_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     post = db.query(MedicinePost).filter(MedicinePost.id == post_id).first()
#     if not post:
#         raise HTTPException(status_code=404, detail="Medicine post not found")
#     if post.status != MedicineStatus.available:  # type: ignore
#         raise HTTPException(status_code=400, detail="Medicine is no longer available")
#     if post.user_id == current_user.id: # type: ignore
#         raise HTTPException(status_code=400, detail="You cannot request your own post")

#     existing = db.query(MedicineRequest).filter(
#         MedicineRequest.medicine_id == post_id,
#         MedicineRequest.requester_id == current_user.id,
#     ).first()
#     if existing:
#         raise HTTPException(status_code=400, detail="You already requested this medicine")

#     req = MedicineRequest(medicine_id=post_id, requester_id=current_user.id)
#     db.add(req)
#     db.commit()
#     db.refresh(req)
#     return req


# @medicine_router.patch("/requests/{request_id}", response_model=MedicineRequestModel)
# def update_medicine_request(
#     request_id: UUID,
#     body: MedicineRequestUpdateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     req = db.query(MedicineRequest).filter(MedicineRequest.id == request_id).first()
#     if not req:
#         raise HTTPException(status_code=404, detail="Request not found")
#     if req.medicine.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Only the post owner can accept/reject requests")
#     req.status = body.status  # type: ignore
#     if body.status.value == "accepted":
#         req.medicine.status = MedicineStatus.claimed  # type: ignore
#     db.commit()
#     db.refresh(req)
#     return req


# # ───────────────────────────────────────────────
# # Lost & Found
# # ───────────────────────────────────────────────

# lost_found_router = APIRouter(prefix="/lost-found", tags=["Lost and Found"])

# @lost_found_router.post("", response_model=LostFoundPostModel, status_code=status.HTTP_201_CREATED)
# def create_lost_found_post(
#     body: LostFoundPostCreateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     post = LostFoundPost(user_id=current_user.id, **body.model_dump())
#     db.add(post)
#     db.commit()
#     db.refresh(post)
#     return post


# @lost_found_router.get("", response_model=List[LostFoundPostModel])
# def get_lost_found_posts(
#     lat: Optional[float] = None,
#     lng: Optional[float] = None,
#     radius_km: float = Query(default=2.0, le=50.0),
#     type: Optional[str] = None,
#     category: Optional[str] = None,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     query = db.query(LostFoundPost).filter(LostFoundPost.status == LostFoundStatus.open)
#     if type:
#         query = query.filter(LostFoundPost.type == type)
#     if category:
#         query = query.filter(LostFoundPost.category == category)
#     posts = query.all()
#     if lat and lng:
#         posts = [
#             p for p in posts
#             if p.lat is not None and p.lng is not None
#             and haversine_km(lat, lng, p.lat, p.lng) <= radius_km  # type: ignore
#         ]
#     return posts


# @lost_found_router.get("/{post_id}", response_model=LostFoundPostModel)
# def get_lost_found_post(
#     post_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     post = db.query(LostFoundPost).filter(LostFoundPost.id == post_id).first()
#     if not post:
#         raise HTTPException(status_code=404, detail="Post not found")
#     return post


# @lost_found_router.patch("/{post_id}", response_model=LostFoundPostModel)
# def update_lost_found_post(
#     post_id: UUID,
#     body: LostFoundPostUpdateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     post = db.query(LostFoundPost).filter(LostFoundPost.id == post_id).first()
#     if not post:
#         raise HTTPException(status_code=404, detail="Post not found")
#     if post.user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your post")
#     for field, value in body.model_dump(exclude_none=True).items():
#         setattr(post, field, value)
#     db.commit()
#     db.refresh(post)
#     return post


# @lost_found_router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_lost_found_post(
#     post_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     post = db.query(LostFoundPost).filter(LostFoundPost.id == post_id).first()
#     if not post:
#         raise HTTPException(status_code=404, detail="Post not found")
#     if post.user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your post")
#     db.delete(post)
#     db.commit()


# # ───────────────────────────────────────────────
# # Hazard Alerts
# # ───────────────────────────────────────────────

# hazard_router = APIRouter(prefix="/hazards", tags=["Hazard Alerts"])

# @hazard_router.post("", response_model=HazardAlertModel, status_code=status.HTTP_201_CREATED)
# def create_hazard_alert(
#     body: HazardAlertCreateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     alert = HazardAlert(user_id=current_user.id, **body.model_dump())
#     db.add(alert)
#     db.commit()
#     db.refresh(alert)
#     return alert


# @hazard_router.get("", response_model=List[HazardAlertModel])
# def get_hazard_alerts(
#     lat: Optional[float] = None,
#     lng: Optional[float] = None,
#     radius_km: float = Query(default=2.0, le=50.0),
#     category: Optional[str] = None,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     query = db.query(HazardAlert).filter(HazardAlert.is_resolved == False)
#     if category:
#         query = query.filter(HazardAlert.category == category)
#     alerts = query.all()
#     if lat and lng:
#         alerts = [
#             a for a in alerts
#             if haversine_km(lat, lng, a.lat, a.lng) <= radius_km
#         ]
#     return alerts


# @hazard_router.get("/{alert_id}", response_model=HazardAlertModel)
# def get_hazard_alert(
#     alert_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     alert = db.query(HazardAlert).filter(HazardAlert.id == alert_id).first()
#     if not alert:
#         raise HTTPException(status_code=404, detail="Hazard alert not found")
#     return alert


# @hazard_router.post("/{alert_id}/confirm", response_model=HazardConfirmationModel, status_code=status.HTTP_201_CREATED)
# def confirm_hazard(
#     alert_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     alert = db.query(HazardAlert).filter(HazardAlert.id == alert_id).first()
#     if not alert:
#         raise HTTPException(status_code=404, detail="Hazard alert not found")
#     if alert.user_id == current_user.id: # type: ignore
#         raise HTTPException(status_code=400, detail="You cannot confirm your own alert")

#     already = db.query(HazardConfirmation).filter(
#         HazardConfirmation.hazard_id == alert_id,
#         HazardConfirmation.user_id == current_user.id,
#     ).first()
#     if already:
#         raise HTTPException(status_code=400, detail="You already confirmed this hazard")

#     confirmation = HazardConfirmation(hazard_id=alert_id, user_id=current_user.id)
#     db.add(confirmation)
#     alert.confirm_count += 1  # type: ignore
#     db.commit()
#     db.refresh(confirmation)
#     return confirmation


# @hazard_router.patch("/{alert_id}", response_model=HazardAlertModel)
# def update_hazard_alert(
#     alert_id: UUID,
#     body: HazardAlertUpdateModel,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     alert = db.query(HazardAlert).filter(HazardAlert.id == alert_id).first()
#     if not alert:
#         raise HTTPException(status_code=404, detail="Hazard alert not found")
#     if alert.user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your alert")
#     for field, value in body.model_dump(exclude_none=True).items():
#         setattr(alert, field, value)
#     db.commit()
#     db.refresh(alert)
#     return alert


# @hazard_router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_hazard_alert(
#     alert_id: UUID,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     alert = db.query(HazardAlert).filter(HazardAlert.id == alert_id).first()
#     if not alert:
#         raise HTTPException(status_code=404, detail="Hazard alert not found")
#     if alert.user_id != current_user.id: # type: ignore
#         raise HTTPException(status_code=403, detail="Not your alert")
#     db.delete(alert)
#     db.commit()