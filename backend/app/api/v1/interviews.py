from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.errors import NotFound
from app.db.session import get_db
from app.models.application import Interview, JobApplication
from app.models.user import User
from app.schemas.misc import InterviewIn, InterviewOut
from app.services.applications.service import get_application

router = APIRouter(prefix="/interviews", tags=["interviews"])


def _out(i: Interview) -> InterviewOut:
    return InterviewOut(id=i.id, application_id=i.application_id, interview_date=i.interview_date, interview_type=i.interview_type,
                        meeting_link=i.meeting_link, notes=i.notes, job_title=i.application.job_title, company_name=i.application.company_name)


def _get(db: Session, user: User, interview_id: int) -> Interview:
    i = db.scalar(select(Interview).join(JobApplication).options(joinedload(Interview.application))
                  .where(Interview.id == interview_id, JobApplication.user_id == user.id))
    if i is None:
        raise NotFound("Interview not found")
    return i


@router.get("", response_model=List[InterviewOut])
def list_interviews(upcoming: bool = False, limit: int = Query(100, ge=1, le=200), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Interview).join(JobApplication).options(joinedload(Interview.application)).where(JobApplication.user_id == user.id)
    if upcoming:
        stmt = stmt.where(Interview.interview_date >= datetime.now(timezone.utc))
    order = Interview.interview_date.asc() if upcoming else Interview.interview_date.desc()
    return [_out(i) for i in db.scalars(stmt.order_by(order).limit(limit))]


@router.post("", response_model=InterviewOut, status_code=201)
def create_interview(data: InterviewIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_application(db, user.id, data.application_id)
    i = Interview(**data.model_dump())
    db.add(i)
    db.commit()
    return _out(_get(db, user, i.id))


@router.put("/{interview_id}", response_model=InterviewOut)
def update_interview(interview_id: int, data: InterviewIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    i = _get(db, user, interview_id)
    get_application(db, user.id, data.application_id)
    for key, value in data.model_dump().items():
        setattr(i, key, value)
    db.commit()
    return _out(_get(db, user, interview_id))


@router.delete("/{interview_id}", status_code=204)
def delete_interview(interview_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.delete(_get(db, user, interview_id))
    db.commit()
