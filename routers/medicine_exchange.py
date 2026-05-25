from uuid import UUID
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from database_models import (
    UserModel as User,
    MedicinePostModel as MedicinePost,
    MedicineRequestModel as MedicineRequest,
    MedicineStatus
)
from schemas import (
    MedicinePostCreateModel, MedicinePostUpdateModel, MedicinePostModel,
    MedicineRequestUpdateModel, MedicineRequestModel,

)
from routers.auth import get_current_user
# ───────────────────────────────────────────────
# Medicine Exchange
# ───────────────────────────────────────────────

medicine_router = APIRouter(prefix="/medicine", tags=["Medicine Exchange"])

@medicine_router.post("", response_model=MedicinePostModel, status_code=status.HTTP_201_CREATED)
def create_medicine_post(
    body: MedicinePostCreateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = MedicinePost(user_id=current_user.id, **body.model_dump())
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@medicine_router.get("", response_model=List[MedicinePostModel])
def get_medicine_posts(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = Query(default=2.0, le=50.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    posts = db.query(MedicinePost).filter(
        MedicinePost.status == MedicineStatus.available,
        MedicinePost.expiry_date >= today,
    ).all()
    if lat and lng:
        posts = [
            p for p in posts
            if p.lat is not None and p.lng is not None
            and haversine_km(lat, lng, p.lat, p.lng) <= radius_km  # type: ignore
        ]
    return posts


@medicine_router.get("/{post_id}", response_model=MedicinePostModel)
def get_medicine_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(MedicinePost).filter(MedicinePost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Medicine post not found")
    return post


@medicine_router.patch("/{post_id}", response_model=MedicinePostModel)
def update_medicine_post(
    post_id: UUID,
    body: MedicinePostUpdateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(MedicinePost).filter(MedicinePost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Medicine post not found")
    if post.user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your post")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(post, field, value)
    db.commit()
    db.refresh(post)
    return post


@medicine_router.delete("/{post_id}")
def delete_medicine_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(MedicinePost).filter(MedicinePost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Medicine post not found")
    if post.user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your post")
    db.delete(post)
    db.commit()
    return {"message": "Medicine post deleted"}


@medicine_router.post("/{post_id}/request", response_model=MedicineRequestModel, status_code=status.HTTP_201_CREATED)
def request_medicine(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(MedicinePost).filter(MedicinePost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Medicine post not found")
    if post.status != MedicineStatus.available:  # type: ignore
        raise HTTPException(status_code=400, detail="Medicine is no longer available")
    if post.user_id == current_user.id: # type: ignore
        raise HTTPException(status_code=400, detail="You cannot request your own post")

    existing = db.query(MedicineRequest).filter(
        MedicineRequest.medicine_id == post_id,
        MedicineRequest.requester_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already requested this medicine")

    req = MedicineRequest(medicine_id=post_id, requester_id=current_user.id)
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@medicine_router.patch("/requests/{request_id}", response_model=MedicineRequestModel)
def update_medicine_request(
    request_id: UUID,
    body: MedicineRequestUpdateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = db.query(MedicineRequest).filter(MedicineRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.medicine.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the post owner can accept/reject requests")
    req.status = body.status  # type: ignore
    if body.status.value == "accepted":
        req.medicine.status = MedicineStatus.claimed  # type: ignore
    db.commit()
    db.refresh(req)
    return req
