from math import radians, sin, cos, asin, sqrt
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from database_models import UserModel as User

def haversine_km(lat1, lng1, lat2, lng2) -> float:
    R = 6371
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return R * 2 * asin(sqrt(a))

def get_user_or_404(user_id: UUID, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user