from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFound
from app.models.application import ApplicationEmail
from app.models.email import Email
from app.models.enums import CATEGORY_LABELS
from app.schemas.email import ApplicationRef, EmailOut


def email_to_out(e: Email) -> EmailOut:
    return EmailOut(
        id=e.id, gmail_message_id=e.gmail_message_id, gmail_thread_id=e.gmail_thread_id,
        sender=e.sender, subject=e.subject, excerpt=e.email_body_excerpt, received_at=e.received_at,
        classification=e.classification, classification_label=CATEGORY_LABELS.get(e.classification, e.classification),
        classification_confidence=e.classification_confidence, extracted_company=e.extracted_company,
        extracted_job_title=e.extracted_job_title, processing_status=e.processing_status,
        applications=[ApplicationRef(id=l.application.id, job_title=l.application.job_title, company_name=l.application.company_name,
                                     confidence=l.match_confidence) for l in e.links],
    )


def _load():
    return selectinload(Email.links).selectinload(ApplicationEmail.application)


def get_email(db: Session, user_id: int, email_id: int) -> Email:
    e = db.scalar(select(Email).options(_load()).where(Email.id == email_id, Email.user_id == user_id))
    if e is None:
        raise NotFound("Email not found")
    return e


def list_emails(
    db: Session, user_id: int, *, processing_status: Optional[str], classification: Optional[str],
    application_id: Optional[int], page: int, page_size: int,
) -> Tuple[List[Email], int]:
    stmt = select(Email).where(Email.user_id == user_id)
    if processing_status:
        stmt = stmt.where(Email.processing_status == processing_status)
    if classification:
        stmt = stmt.where(Email.classification == classification)
    if application_id:
        stmt = stmt.where(Email.id.in_(select(ApplicationEmail.email_id).where(ApplicationEmail.application_id == application_id)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.options(_load()).order_by(Email.received_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return list(rows), total
