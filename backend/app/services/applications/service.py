from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, contains_eager

from app.core.errors import Conflict, NotFound
from app.db.base import utcnow
from app.models.application import ApplicationHistory, JobApplication, Platform
from app.models.enums import STATUS_LABELS, ApplicationStatus, ChangeSource
from app.schemas.application import ApplicationCreate, ApplicationUpdate, TimelineEvent


@dataclass
class ApplicationFilters:
    q: Optional[str] = None
    platform_id: Optional[int] = None
    status: Optional[ApplicationStatus] = None
    company: Optional[str] = None
    employment_type: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    sort: str = "newest"
    page: int = 1
    page_size: int = 20


def get_owned_platform(db: Session, user_id: int, platform_id: int) -> Platform:
    platform = db.get(Platform, platform_id)
    if platform is None or platform.user_id not in (None, user_id):
        raise NotFound("Platform not found")
    return platform


def get_application(db: Session, user_id: int, application_id: int) -> JobApplication:
    app = db.scalar(select(JobApplication).where(JobApplication.id == application_id, JobApplication.user_id == user_id))
    if app is None:
        raise NotFound("Application not found")
    return app


def list_applications(db: Session, user_id: int, f: ApplicationFilters) -> Tuple[List[JobApplication], int]:
    stmt = select(JobApplication).join(Platform, JobApplication.platform_id == Platform.id).where(JobApplication.user_id == user_id)
    if f.q:
        like = f"%{f.q.strip()}%"
        stmt = stmt.where(or_(JobApplication.company_name.ilike(like), JobApplication.job_title.ilike(like), Platform.name.ilike(like)))
    if f.platform_id:
        stmt = stmt.where(JobApplication.platform_id == f.platform_id)
    if f.status:
        stmt = stmt.where(JobApplication.status == f.status.value)
    if f.company:
        stmt = stmt.where(JobApplication.company_name.ilike(f"%{f.company.strip()}%"))
    if f.employment_type:
        stmt = stmt.where(JobApplication.employment_type == f.employment_type)
    if f.date_from:
        stmt = stmt.where(JobApplication.application_date >= f.date_from)
    if f.date_to:
        stmt = stmt.where(JobApplication.application_date <= f.date_to)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    order = {
        "oldest": (JobApplication.application_date.asc(), JobApplication.id.asc()),
        "updated": (JobApplication.updated_at.desc(), JobApplication.id.desc()),
    }.get(f.sort, (JobApplication.application_date.desc(), JobApplication.id.desc()))
    rows = db.scalars(
        stmt.options(contains_eager(JobApplication.platform)).order_by(*order).offset((f.page - 1) * f.page_size).limit(f.page_size)
    ).unique().all()
    return list(rows), total


def change_status(
    db: Session, app: JobApplication, new_status: ApplicationStatus, source: ChangeSource,
    description: Optional[str] = None, at: Optional[datetime] = None,
) -> bool:
    """Set the status and record it in history. The caller owns the transaction (commit)."""
    if app.status == new_status.value:
        return False
    db.add(ApplicationHistory(
        application_id=app.id, previous_status=app.status, new_status=new_status.value,
        change_source=source.value, description=description, created_at=at or utcnow(),
    ))
    app.status = new_status.value
    app.updated_at = utcnow()
    db.flush()
    return True


def create_application(db: Session, user_id: int, data: ApplicationCreate) -> JobApplication:
    get_owned_platform(db, user_id, data.platform_id)
    values = data.model_dump(mode="json")
    app = JobApplication(user_id=user_id, **{**values, "application_date": data.application_date})
    db.add(app)
    db.flush()
    submitted = data.status != ApplicationStatus.SAVED
    db.add(ApplicationHistory(
        application_id=app.id, previous_status=None, new_status=app.status, change_source=ChangeSource.MANUAL.value,
        description="Application submitted" if submitted else "Job saved",
        created_at=datetime.combine(data.application_date, time.min, tzinfo=timezone.utc),
    ))
    db.commit()
    return app


def update_application(db: Session, user_id: int, application_id: int, data: ApplicationUpdate) -> JobApplication:
    app = get_application(db, user_id, application_id)
    get_owned_platform(db, user_id, data.platform_id)
    values = data.model_dump(mode="json", exclude={"status"})
    values["application_date"] = data.application_date
    for key, value in values.items():
        setattr(app, key, value)
    change_status(db, app, data.status, ChangeSource.MANUAL, "Status edited")
    app.updated_at = utcnow()
    db.commit()
    return app


def delete_application(db: Session, user_id: int, application_id: int) -> None:
    db.delete(get_application(db, user_id, application_id))
    db.commit()


def update_status(db: Session, user_id: int, application_id: int, status: ApplicationStatus, note: Optional[str]) -> JobApplication:
    app = get_application(db, user_id, application_id)
    change_status(db, app, status, ChangeSource.MANUAL, note or "Status changed manually")
    db.commit()
    return app


def build_timeline(app: JobApplication) -> List[TimelineEvent]:
    events: List[TimelineEvent] = []
    for i, h in enumerate(app.history):
        label = STATUS_LABELS.get(h.new_status, h.new_status)
        initial = h.previous_status is None
        events.append(TimelineEvent(
            kind="submitted" if initial else "status", at=h.created_at,
            title=h.description or "Application added" if initial else f"Status changed to {label}",
            description=None if initial else h.description, status=h.new_status, source=h.change_source,
        ))
    for link in app.email_links:
        e = link.email
        events.append(TimelineEvent(kind="email", at=e.received_at, title=e.subject or "(no subject)", description=e.sender, source="gmail"))
    for iv in app.interviews:
        events.append(TimelineEvent(kind="interview", at=iv.interview_date, title="Interview scheduled", description=iv.interview_type))

    def key(ev: TimelineEvent):
        return ev.at.replace(tzinfo=None) if ev.at.tzinfo else ev.at

    return sorted(events, key=key)


def delete_platform_guard(db: Session, platform: Platform) -> None:
    in_use = db.scalar(select(func.count()).select_from(JobApplication).where(JobApplication.platform_id == platform.id))
    if in_use:
        raise Conflict("This platform still has applications. Move or delete them first.")
