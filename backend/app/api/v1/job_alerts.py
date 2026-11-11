from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.job_alert import JobAlertPage
from app.services import job_alerts as svc

router = APIRouter(prefix="/job-alerts", tags=["job alerts"])


@router.get("", response_model=JobAlertPage)
def list_job_alerts(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    rows, total = svc.list_alerts(db, user.id, page, page_size)
    return JobAlertPage(items=[svc.alert_to_out(alert) for alert in rows], total=total, page=page, page_size=page_size)
