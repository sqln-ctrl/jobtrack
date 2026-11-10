from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import Conflict, NotFound
from app.db.session import get_db
from app.models.application import Platform
from app.models.user import User
from app.schemas.application import PlatformIn, PlatformOut
from app.services.applications.service import delete_platform_guard

router = APIRouter(prefix="/platforms", tags=["platforms"])

DEFAULT_PLATFORMS = ["LinkedIn", "Indeed", "Glassdoor", "Rozee.pk", "Company Website", "Direct Email", "Other"]


def seed_default_platforms(db: Session) -> None:
    existing = set(db.scalars(select(Platform.name).where(Platform.user_id.is_(None))))
    for name in DEFAULT_PLATFORMS:
        if name not in existing:
            db.add(Platform(name=name, user_id=None))
    db.commit()


def _own(db: Session, user: User, platform_id: int) -> Platform:
    p = db.scalar(select(Platform).where(Platform.id == platform_id, Platform.user_id == user.id))
    if p is None:
        raise NotFound("Custom platform not found")  # defaults and other users' platforms are not editable
    return p


def _ensure_unique(db: Session, user: User, name: str, exclude_id: int = 0) -> None:
    clash = db.scalar(select(Platform.id).where(
        Platform.id != exclude_id, or_(Platform.user_id.is_(None), Platform.user_id == user.id), Platform.name.ilike(name)))
    if clash:
        raise Conflict("A platform with this name already exists")


@router.get("", response_model=List[PlatformOut])
def list_platforms(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Platform).where(or_(Platform.user_id.is_(None), Platform.user_id == user.id)).order_by(Platform.user_id.is_not(None), Platform.id)).all()


@router.post("", response_model=PlatformOut, status_code=201)
def create_platform(data: PlatformIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_unique(db, user, data.name)
    p = Platform(name=data.name, user_id=user.id)
    db.add(p)
    db.commit()
    return p


@router.put("/{platform_id}", response_model=PlatformOut)
def update_platform(platform_id: int, data: PlatformIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = _own(db, user, platform_id)
    _ensure_unique(db, user, data.name, exclude_id=p.id)
    p.name = data.name
    db.commit()
    return p


@router.delete("/{platform_id}", status_code=204)
def delete_platform(platform_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = _own(db, user, platform_id)
    delete_platform_guard(db, p)
    db.delete(p)
    db.commit()
