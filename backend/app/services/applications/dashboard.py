from datetime import date, datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.application import ApplicationHistory, Interview, JobApplication, Platform
from app.models.email import Email
from app.models.enums import STATUS_LABELS, ApplicationStatus, ProcessingStatus

PIPELINE = ["sent", "viewed", "interview_call", "accepted", "rejected"]


def status_counts(db: Session, user_id: int) -> Dict[str, int]:
    rows = db.execute(select(JobApplication.status, func.count()).where(JobApplication.user_id == user_id).group_by(JobApplication.status)).all()
    counts = {s: 0 for s in PIPELINE}
    counts.update({status: n for status, n in rows})
    return counts


def stats(db: Session, user_id: int) -> dict:
    counts = status_counts(db, user_id)
    week_start = date.today() - timedelta(days=date.today().weekday())
    this_week = db.scalar(select(func.count()).select_from(JobApplication).where(
        JobApplication.user_id == user_id, JobApplication.application_date >= week_start)) or 0
    upcoming = db.scalar(select(func.count()).select_from(Interview).join(JobApplication).where(
        JobApplication.user_id == user_id, Interview.interview_date >= datetime.now(timezone.utc))) or 0
    needs_review = db.scalar(select(func.count()).select_from(Email).where(
        Email.user_id == user_id, Email.processing_status == ProcessingStatus.NEEDS_REVIEW.value)) or 0
    return {
        "total": sum(counts.values()), "this_week": this_week, "interview_calls": counts["interview_call"],
        "upcoming_interviews": upcoming, "accepted": counts["accepted"], "rejected": counts["rejected"],
        "awaiting_response": counts["sent"] + counts["viewed"], "emails_needing_review": needs_review,
    }


def platform_distribution(db: Session, user_id: int) -> List[dict]:
    rows = db.execute(
        select(Platform.id, Platform.name, func.count(JobApplication.id)).join(JobApplication, JobApplication.platform_id == Platform.id)
        .where(JobApplication.user_id == user_id).group_by(Platform.id, Platform.name).order_by(func.count(JobApplication.id).desc())
    ).all()
    return [{"platform_id": pid, "name": name, "count": n} for pid, name, n in rows]


def status_distribution(db: Session, user_id: int) -> List[dict]:
    counts = status_counts(db, user_id)
    return [{"status": s, "label": STATUS_LABELS[s], "count": counts[s]} for s in PIPELINE]


def recent_status_changes(db: Session, user_id: int, limit: int = 8) -> List[dict]:
    rows = db.scalars(
        select(ApplicationHistory).join(JobApplication).options(joinedload(ApplicationHistory.application))
        .where(JobApplication.user_id == user_id, ApplicationHistory.previous_status.is_not(None))
        .order_by(ApplicationHistory.created_at.desc()).limit(limit)
    ).all()
    return [{
        "application_id": h.application_id, "job_title": h.application.job_title, "company_name": h.application.company_name,
        "previous_status": h.previous_status, "new_status": h.new_status, "source": h.change_source, "at": h.created_at,
    } for h in rows]
