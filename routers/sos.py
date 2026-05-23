import datetime
from fastapi import APIRouter
from requests import Session
from uuid import UUID
from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from database_models import (
    UserModel as User,
    SOSEventModel as SOSEvent,
    SOSNotificationModel as SOSNotification,
    SOSStatus, SOSNotificationType, SOSResponseStatus,
)
from helpers import haversine_km
from schemas import (
    SOSCreateModel, SOSUpdateModel, SOSEventModel,
    SOSNotificationModel, SOSNotificationRespondModel,
)

from routers.auth import get_current_user

sos_router = APIRouter(prefix="/sos", tags=["SOS"])

SOS_VOLUNTEER_RADIUS_KM  = 2.0
SOS_VOLUNTEER_EXPAND_KM  = [5.0, 10.0]
SOS_COOLDOWN_MINUTES     = 30
SOS_MAX_VOLUNTEERS_PINGED = 3

def notify_nearby_volunteers(sos: SOSEvent, db: Session):
    radii = [SOS_VOLUNTEER_RADIUS_KM] + SOS_VOLUNTEER_EXPAND_KM
    cooldown_cutoff = datetime.utcnow() - timedelta(minutes=SOS_COOLDOWN_MINUTES)

    volunteers = db.query(User).filter(
        User.is_volunteer == True,
        User.volunteer_available == True,
        User.lat.isnot(None),
        User.lng.isnot(None),
        User.id != sos.user_id,
        (User.last_sos_at == None) | (User.last_sos_at < cooldown_cutoff)
    ).all()

    selected = []
    for radius in radii:
        nearby = [v for v in volunteers if haversine_km(sos.lat, sos.lng, v.lat, v.lng) <= radius]
        nearby.sort(key=lambda v: v.last_sos_at or datetime.min)
        selected = nearby[:SOS_MAX_VOLUNTEERS_PINGED]
        if selected:
            break

    for volunteer in selected:
        notif = SOSNotification(
            sos_id=sos.id,
            notified_user_id=volunteer.id,
            type=SOSNotificationType.volunteer,
            response_status=SOSResponseStatus.pending,
        )
        db.add(notif)
        volunteer.last_sos_at = datetime.utcnow()  # type: ignore

    db.commit()
    return selected


@sos_router.post("", response_model=SOSEventModel, status_code=status.HTTP_201_CREATED)
def trigger_sos(
    body: SOSCreateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.sos_false_alarm_count >= 3:  # type: ignore
        raise HTTPException(status_code=403, detail="Account flagged for repeated false SOS alarms")

    sos = SOSEvent(
        user_id=current_user.id,
        message=body.message,
        voice_url=body.voice_url,
        lat=body.lat,
        lng=body.lng,
        share_live_location=body.share_live_location,
        status=SOSStatus.active,
    )
    db.add(sos)
    db.commit()
    db.refresh(sos)
    notify_nearby_volunteers(sos, db)
    return sos


@sos_router.patch("/{sos_id}/resolve", response_model=SOSEventModel)
def resolve_sos(
    sos_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sos = db.query(SOSEvent).filter(SOSEvent.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS event not found")
    if sos.user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your SOS event")
    sos.status = SOSStatus.resolved  # type: ignore
    sos.resolved_at = datetime.utcnow()  # type: ignore
    db.commit()
    db.refresh(sos)
    return sos


@sos_router.patch("/{sos_id}/false-alarm", response_model=SOSEventModel)
def mark_false_alarm(
    sos_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_volunteer: # type: ignore
        raise HTTPException(status_code=403, detail="Only volunteers can mark false alarms")
    sos = db.query(SOSEvent).filter(SOSEvent.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS event not found")
    sos.status = SOSStatus.false_alarm  # type: ignore
    sos.resolved_at = datetime.utcnow()  # type: ignore
    user = get_user_or_404(sos.user_id, db)  # type: ignore
    user.sos_false_alarm_count += 1  # type: ignore
    db.commit()
    db.refresh(sos)
    return sos


@sos_router.patch("/notifications/{notif_id}/respond", response_model=SOSNotificationModel)
def respond_to_sos(
    notif_id: UUID,
    body: SOSNotificationRespondModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = db.query(SOSNotification).filter(SOSNotification.id == notif_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notif.notified_user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your notification")
    notif.response_status = body.response_status  # type: ignore
    notif.responded_at = datetime.utcnow()  # type: ignore
    db.commit()
    db.refresh(notif)
    return notif


@sos_router.patch("/{sos_id}/location", response_model=SOSEventModel)
def update_sos_location(
    sos_id: UUID,
    body: SOSUpdateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sos = db.query(SOSEvent).filter(SOSEvent.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS event not found")
    if sos.user_id != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not your SOS event")
    if body.lat:
        sos.lat = body.lat  # type: ignore
    if body.lng:
        sos.lng = body.lng  # type: ignore
    db.commit()
    db.refresh(sos)
    return sos


@sos_router.get("/history", response_model=List[SOSEventModel])
def get_my_sos_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(SOSEvent).filter(SOSEvent.user_id == current_user.id).all()
