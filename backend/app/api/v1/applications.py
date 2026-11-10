from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import ApplicationStatus
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationOut, ApplicationPage, ApplicationUpdate, StatusUpdate
from app.schemas.misc import ApplicationDetail, InterviewOut
from app.services.applications import service
from app.services.applications.emails import email_to_out

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=ApplicationPage)
def list_applications(
    q: Optional[str] = None, platform_id: Optional[int] = None, status: Optional[ApplicationStatus] = None,
    company: Optional[str] = None, employment_type: Optional[str] = None, date_from: Optional[date] = None,
    date_to: Optional[date] = None, sort: str = Query("newest", pattern="^(newest|oldest|updated)$"),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    filters = service.ApplicationFilters(q, platform_id, status, company, employment_type, date_from, date_to, sort, page, page_size)
    items, total = service.list_applications(db, user.id, filters)
    return ApplicationPage(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ApplicationOut, status_code=201)
def create_application(data: ApplicationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.create_application(db, user.id, data)


@router.get("/{application_id}", response_model=ApplicationDetail)
def get_application(application_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    app = service.get_application(db, user.id, application_id)
    interviews = [InterviewOut(**{c: getattr(i, c) for c in ("id", "application_id", "interview_date", "interview_type", "meeting_link", "notes")},
                               job_title=app.job_title, company_name=app.company_name) for i in app.interviews]
    emails = sorted((l.email for l in app.email_links), key=lambda e: e.received_at, reverse=True)
    return ApplicationDetail(application=app, timeline=service.build_timeline(app), emails=[email_to_out(e) for e in emails], interviews=interviews)


@router.put("/{application_id}", response_model=ApplicationOut)
def update_application(application_id: int, data: ApplicationUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.update_application(db, user.id, application_id, data)


@router.delete("/{application_id}", status_code=204)
def delete_application(application_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service.delete_application(db, user.id, application_id)


@router.patch("/{application_id}/status", response_model=ApplicationOut)
def update_status(application_id: int, data: StatusUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.update_status(db, user.id, application_id, data.status, data.note)
