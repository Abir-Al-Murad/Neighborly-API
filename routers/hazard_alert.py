from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from database_models import (
    UserModel as User,
    HazardAlertModel as HazardAlert,
    HazardConfirmationModel as HazardConfirmation,

)
from helpers import haversine_km
from schemas import (
    HazardAlertCreateModel, HazardAlertUpdateModel, HazardAlertModel, HazardConfirmationModel
)
from routers.auth import get_current_user

# ───────────────────────────────────────────────
# Hazard Alerts
# ───────────────────────────────────────────────

hazard_router = APIRouter(prefix="/hazards", tags=["Hazard Alerts"])

@hazard_router.post("", response_model=HazardAlertModel, status_code=status.HTTP_201_CREATED)
def create_hazard_alert(
    body: HazardAlertCreateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = HazardAlert(user_id=current_user.id, **body.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@hazard_router.get("", response_model=List[HazardAlertModel])
def get_hazard_alerts(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = Query(default=2.0, le=50.0),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(HazardAlert).filter(HazardAlert.is_resolved == False)
    if category:
        query = query.filter(HazardAlert.category == category)
    alerts = query.all()
    if lat and lng:
        alerts = [
            a for a in alerts
            if haversine_km(lat, lng, a.lat, a.lng) <= radius_km
        ]
    return alerts


@hazard_router.get("/{alert_id}", response_model=HazardAlertModel)
def get_hazard_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(HazardAlert).filter(HazardAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Hazard alert not found")
    return alert


@hazard_router.post("/{alert_id}/confirm", response_model=HazardConfirmationModel, status_code=status.HTTP_201_CREATED)
def confirm_hazard(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(HazardAlert).filter(HazardAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Hazard alert not found")
    if alert.user_id == current_user.id: # type: ignore
        raise HTTPException(status_code=400, detail="You cannot confirm your own alert")

    already = db.query(HazardConfirmation).filter(
        HazardConfirmation.hazard_id == alert_id,
        HazardConfirmation.user_id == current_user.id,
    ).first()
    if already:
        raise HTTPException(status_code=400, detail="You already confirmed this hazard")

    confirmation = HazardConfirmation(hazard_id=alert_id, user_id=current_user.id)
    db.add(confirmation)
    alert.confirm_count += 1  # type: ignore
    db.commit()
    db.refresh(confirmation)
    return confirmation


@hazard_router.patch("/{alert_id}", response_model=HazardAlertModel)
def update_hazard_alert(
    alert_id: UUID,
    body: HazardAlertUpdateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(HazardAlert).filter(HazardAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Hazard alert not found")
    if alert.user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your alert")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(alert, field, value)
    db.commit()
    db.refresh(alert)
    return alert


@hazard_router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hazard_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(HazardAlert).filter(HazardAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Hazard alert not found")
    if alert.user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your alert")
    db.delete(alert)
    db.commit()