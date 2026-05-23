
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from database_models import (
    UserModel as User,
    HomeListingModel as HomeListing,
    HomePhotoModel as HomePhoto,
)

from schemas import (
    HomeListingCreateModel, HomeListingUpdateModel, HomeListingModel, HomePhotoModel,
)
from routers.auth import get_current_user
# ───────────────────────────────────────────────
# Home Listings
# ───────────────────────────────────────────────

home_router = APIRouter(prefix="/home", tags=["Home Listings"])

@home_router.post("", response_model=HomeListingModel, status_code=status.HTTP_201_CREATED)
def create_listing(
    body: HomeListingCreateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    listing = HomeListing(user_id=current_user.id, **body.model_dump())
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@home_router.get("", response_model=List[HomeListingModel])
def get_listings(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = Query(default=2.0, le=50.0),
    area: Optional[str] = None,
    low_price: Optional[float] = None,
    high_price: Optional[float] = None,
    listing_type: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(HomeListing).filter(
        HomeListing.is_active.is_(True)
    )

    if listing_type:
        query = query.filter(HomeListing.listing_type == listing_type)
    if low_price is not None:
        query = query.filter(HomeListing.price >= low_price)
    if high_price is not None:
        query = query.filter(HomeListing.price <= high_price)
    if area:
        query = query.filter(HomeListing.area_name.ilike(f"%{area}%"))

    # ✅ DB-তেই haversine filter — তোমার existing formula হুবহু SQL-এ
    if lat is not None and lng is not None:
        query = query.filter(
            HomeListing.lat.isnot(None),
            HomeListing.lng.isnot(None),
            (6371 * 2 * func.asin(func.sqrt(
                func.pow(func.sin(func.radians(HomeListing.lat - lat) / 2), 2) +
                func.cos(func.radians(lat)) *
                func.cos(func.radians(HomeListing.lat)) *
                func.pow(func.sin(func.radians(HomeListing.lng - lng) / 2), 2)
            ))) <= radius_km
        )

    # ✅ এখন pagination সঠিকভাবে কাজ করবে
    offset = (page - 1) * page_size
    listings = query.offset(offset).limit(page_size).all()

    return listings
@home_router.get("/{listing_id}", response_model=HomeListingModel)
def get_listing(
    listing_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    listing = db.query(HomeListing).filter(HomeListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@home_router.patch("/{listing_id}", response_model=HomeListingModel)
def update_listing(
    listing_id: UUID,
    body: HomeListingUpdateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    listing = db.query(HomeListing).filter(HomeListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your listing")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(listing, field, value)
    db.commit()
    db.refresh(listing)
    return listing


@home_router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(
    listing_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    listing = db.query(HomeListing).filter(HomeListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your listing")
    db.delete(listing)
    db.commit()


@home_router.post("/{listing_id}/photos", response_model=HomePhotoModel, status_code=status.HTTP_201_CREATED)
def add_photo(
    listing_id: UUID,
    photo_url: str,
    sort_order: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    listing = db.query(HomeListing).filter(HomeListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your listing")
    photo = HomePhoto(listing_id=listing_id, photo_url=photo_url, sort_order=sort_order)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo

