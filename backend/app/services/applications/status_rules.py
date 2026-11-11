"""When may an email move an application's status? Email updates only move forward."""
from typing import Optional

from app.models.enums import ApplicationStatus as S, EmailCategory as C

EARLY = {S.SENT}


def next_status_for(category: C, current: S) -> Optional[S]:
    if category in (C.APPLICATION_CONFIRMATION, C.APPLICATION_RECEIVED):
        return S.SENT if current == S.SENT else None
    if category == C.UNDER_REVIEW:
        return S.VIEWED if current in EARLY else None
    if category == C.ASSESSMENT_INVITATION:
        return S.VIEWED if current in EARLY else None
    if category == C.INTERVIEW_INVITATION:
        return S.INTERVIEW_CALL if current in EARLY | {S.VIEWED} else None
    if category == C.JOB_OFFER:
        return S.ACCEPTED if current != S.ACCEPTED else None
    return None
