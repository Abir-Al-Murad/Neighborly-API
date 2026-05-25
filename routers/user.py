# ───────────────────────────────────────────────
# Users
# ───────────────────────────────────────────────

from uuid import UUID
from fastapi import APIRouter, Depends, Depends,HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database_models import UserModel as User
from schemas import UserModel, UserUpdateModel
from routers.auth import get_current_user
from helpers import get_user_or_404
    
user_router = APIRouter(prefix="/users", tags=["Users"])

@user_router.get("/me", response_model=UserModel)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@user_router.get("/{user_id}", response_model=UserModel)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_or_404(user_id, db)


@user_router.patch("/{user_id}", response_model=UserModel)
def update_user(
    user_id: UUID,
    body: UserUpdateModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id: # type: ignore
        raise HTTPException(status_code=403, detail="You can only update your own profile")
    user = get_user_or_404(user_id, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@user_router.delete("/{user_id}")
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id: # type: ignore
        raise HTTPException(status_code=403, detail="You can only delete your own account")
    user = get_user_or_404(user_id, db)
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}