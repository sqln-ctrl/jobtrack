from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.models.application import ApplicationEmail, JobApplication
from app.models.email import Email
from app.models.enums import ApplicationStatus, ChangeSource, EmailCategory, ProcessingStatus
from app.services.applications.service import change_status
from app.services.applications.status_rules import next_status_for


def link_email(db: Session, email: Email, app: JobApplication, confidence: float) -> bool:
    """Attach an email to an application and apply any status change it justifies.
    Returns True if the status changed. The caller owns the transaction (commit)."""
    link = db.scalar(select(ApplicationEmail).where(ApplicationEmail.application_id == app.id, ApplicationEmail.email_id == email.id))
    if link is None:
        db.add(ApplicationEmail(application_id=app.id, email_id=email.id, match_confidence=confidence))
    else:
        link.match_confidence = confidence
    email.processing_status = ProcessingStatus.MATCHED.value

    new_status = next_status_for(EmailCategory(email.classification), ApplicationStatus(app.status))
    if new_status is None:
        app.updated_at = utcnow()
        return False
    return change_status(db, app, new_status, ChangeSource.GMAIL, f"Detected from email: {email.subject[:120]}", at=email.received_at)
