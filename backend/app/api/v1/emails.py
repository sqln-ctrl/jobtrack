from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.email import EmailOut, EmailPage, MatchRequest
from app.services.applications import emails as svc

router = APIRouter(prefix="/emails", tags=["emails"])


def list_page(db, user, processing_status, classification, application_id, page, page_size) -> EmailPage:
    rows, total = svc.list_emails(db, user.id, processing_status=processing_status, classification=classification,
                                  application_id=application_id, page=page, page_size=page_size)
    return EmailPage(items=[svc.email_to_out(e) for e in rows], total=total, page=page, page_size=page_size)


@router.get("", response_model=EmailPage)
def list_emails(
    processing_status: Optional[str] = Query(None, pattern="^(matched|needs_review|ignored)$"), classification: Optional[str] = None,
    application_id: Optional[int] = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    return list_page(db, user, processing_status, classification, application_id, page, page_size)


@router.get("/{email_id}", response_model=EmailOut)
def get_email(email_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.email_to_out(svc.get_email(db, user.id, email_id))


@router.post("/{email_id}/match", response_model=EmailOut)
def match_email(email_id: int, data: MatchRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.email_to_out(svc.match_email(db, user.id, email_id, data.application_id))


@router.post("/{email_id}/ignore", response_model=EmailOut)
def ignore_email(email_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.email_to_out(svc.ignore_email(db, user.id, email_id))
