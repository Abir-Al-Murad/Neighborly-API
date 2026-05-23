
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from database_models import (
    UserModel as User,
    HomeListingModel as HomeListing,
    HomePhotoModel as HomePhoto,
)
from schemas import (
    HomeListingCreateModel, HomeListingUpdateModel, HomeListingModel, HomePhotoModel,
)
from routerss.auth import get_current_user
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
    listing_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(HomeListing).filter(HomeListing.is_active == True)
    if listing_type:
        query = query.filter(HomeListing.listing_type == listing_type)
    listings = query.all()
    if lat and lng:
        listings = [
            l for l in listings
            if l.lat is not None and l.lng is not None
            and haversine_km(lat, lng, l.lat, l.lng) <= radius_km  # type: ignore
        ]
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

