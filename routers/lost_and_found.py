# ───────────────────────────────────────────────
# Lost & Found
# ───────────────────────────────────────────────

from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from database_models import (
    UserModel as User,
    LostFoundPostModel as LostFoundPost,
    LostFoundStatus
)
from schemas import (
    LostFoundPostCreateModel, LostFoundPostUpdateModel, LostFoundPostModel,
)
from routers.auth import get_current_user
lost_found_router = APIRouter(prefix="/lost-found", tags=["Lost and Found"])

@lost_found_router.post("", response_model=LostFoundPostModel, status_code=status.HTTP_201_CREATED)
def create_lost_found_post(
    body: LostFoundPostCreateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = LostFoundPost(user_id=current_user.id, **body.model_dump())
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@lost_found_router.get("", response_model=List[LostFoundPostModel])
def get_lost_found_posts(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = Query(default=2.0, le=50.0),
    type: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(LostFoundPost).filter(LostFoundPost.status == LostFoundStatus.open)
    if type:
        query = query.filter(LostFoundPost.type == type)
    if category:
        query = query.filter(LostFoundPost.category == category)
    posts = query.all()
    if lat and lng:
        posts = [
            p for p in posts
            if p.lat is not None and p.lng is not None
            and haversine_km(lat, lng, p.lat, p.lng) <= radius_km  # type: ignore
        ]
    return posts


@lost_found_router.get("/{post_id}", response_model=LostFoundPostModel)
def get_lost_found_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(LostFoundPost).filter(LostFoundPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@lost_found_router.patch("/{post_id}", response_model=LostFoundPostModel)
def update_lost_found_post(
    post_id: UUID,
    body: LostFoundPostUpdateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(LostFoundPost).filter(LostFoundPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your post")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(post, field, value)
    db.commit()
    db.refresh(post)
    return post


@lost_found_router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lost_found_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(LostFoundPost).filter(LostFoundPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your post")
    db.delete(post)
    db.commit()
