from uuid import UUID
from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from database_models import (
    BloodGroup,
    UserModel as User,
    BloodDonorModel as BloodDonor,
)
from helpers import haversine_km
from schemas import (
    BloodDonorWithDistanceModel,
    BloodDonorCreateModel, BloodDonorUpdateModel, BloodDonorModel, BloodDonorWithUserModel,

)
from routerss.auth import get_current_user

# ───────────────────────────────────────────────
# Blood Donors
# ───────────────────────────────────────────────

blood_router = APIRouter(prefix="/blood", tags=["Blood Donors"])

@blood_router.post("/register", response_model=BloodDonorModel, status_code=status.HTTP_201_CREATED)
def register_donor(
    body: BloodDonorCreateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(BloodDonor).filter(BloodDonor.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You are already a registered donor")

    donor = BloodDonor(
        user_id=current_user.id,
        blood_group=body.blood_group,
        last_donation_date=body.last_donation_date,
        notes=body.notes,
        lat=body.lat,
        lng=body.lng,
    )
    db.add(donor)
    db.commit()
    db.refresh(donor)
    return donor


@blood_router.get("/search", response_model=List[BloodDonorWithUserModel])
def search_donors(
    blood_group: BloodGroup,
    lat: float,
    lng: float,
    radius_km: float = Query(default=2.0, le=50.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    radii = sorted(set(r for r in [radius_km, 5.0, 10.0] if r >= radius_km))
    donors = db.query(BloodDonor).filter(
        BloodDonor.blood_group == blood_group,
        BloodDonor.is_active == True,
        BloodDonor.lat.isnot(None),
        BloodDonor.lng.isnot(None),
    ).all()

    for radius in radii:
        nearby = [d for d in donors if haversine_km(lat, lng, d.lat, d.lng) <= radius]
        if nearby:
            return nearby
    return []



@blood_router.get(
    "/nearest",
    response_model=List[BloodDonorWithDistanceModel]
)
def get_nearest_donors(
    lat: float,
    lng: float,
    blood_group: Optional[BloodGroup] = None,
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    query = db.query(BloodDonor).filter(
        BloodDonor.is_active == True,
        BloodDonor.lat.isnot(None),
        BloodDonor.lng.isnot(None),
    )

    if blood_group is not None:
        query = query.filter(BloodDonor.blood_group == blood_group)

    donors = query.all()

    donors_with_distance = sorted(
        [
            {
                "distance_km": round(
                    haversine_km(lat, lng, donor.lat, donor.lng),
                    2
                ),
                "donor": donor
            }
            for donor in donors
        ],
        key=lambda x: x["distance_km"]
    )

    return donors_with_distance[:limit]

@blood_router.get("/{donor_id}", response_model=BloodDonorWithUserModel)
def get_donor(
    donor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    donor = db.query(BloodDonor).filter(BloodDonor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    return donor


@blood_router.patch("/{donor_id}", response_model=BloodDonorModel)
def update_donor(
    donor_id: UUID,
    body: BloodDonorUpdateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    donor = db.query(BloodDonor).filter(BloodDonor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    if donor.user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your donor profile")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(donor, field, value)
    db.commit()
    db.refresh(donor)
    return donor


@blood_router.delete("/{donor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_donor(
    donor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    donor = db.query(BloodDonor).filter(BloodDonor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    if donor.user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your donor profile")
    db.delete(donor)
    db.commit()
