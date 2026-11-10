from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.applications import dashboard as svc
from app.services.applications.emails import email_to_out, list_emails

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.stats(db, user.id)


@router.get("/platforms")
def platforms(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.platform_distribution(db, user.id)


@router.get("/status-distribution")
def status_distribution(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.status_distribution(db, user.id)


@router.get("/recent-activity")
def recent_activity(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows, _ = list_emails(db, user.id, processing_status=None, classification=None, application_id=None, page=1, page_size=8)
    return {"emails": [email_to_out(e) for e in rows if e.processing_status != "ignored"], "status_changes": svc.recent_status_changes(db, user.id)}
