"""When may an email move an application's status? Conservative by design: emails only move
applications forward, never overwrite a final outcome, and never downgrade progress."""
from typing import Optional

from app.models.enums import ApplicationStatus as S, EmailCategory as C

EARLY = {S.SAVED, S.APPLIED, S.NO_RESPONSE}


def next_status_for(category: C, current: S) -> Optional[S]:
    if category in (C.APPLICATION_CONFIRMATION, C.APPLICATION_RECEIVED):
        return S.APPLIED if current == S.SAVED else None
    if category == C.UNDER_REVIEW:
        return S.UNDER_REVIEW if current in EARLY else None
    if category == C.ASSESSMENT_INVITATION:
        return S.ASSESSMENT if current in EARLY | {S.UNDER_REVIEW} else None
    if category == C.INTERVIEW_INVITATION:
        return S.INTERVIEW if current in EARLY | {S.UNDER_REVIEW, S.ASSESSMENT} else None
    if category == C.REJECTION:
        return S.REJECTED if current not in {S.REJECTED, S.WITHDRAWN, S.OFFER} else None
    if category == C.JOB_OFFER:
        return S.OFFER if current not in {S.OFFER, S.WITHDRAWN, S.REJECTED} else None
    return None
