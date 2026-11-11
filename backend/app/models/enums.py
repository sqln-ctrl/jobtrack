from enum import Enum


class ApplicationStatus(str, Enum):
    SENT = "sent"
    VIEWED = "viewed"
    INTERVIEW_CALL = "interview_call"
    ACCEPTED = "accepted"


STATUS_LABELS = {
    "sent": "Sent", "viewed": "Viewed", "interview_call": "Interview call", "accepted": "Accepted",
}


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"
    TEMPORARY = "temporary"
    OTHER = "other"


class EmailCategory(str, Enum):
    APPLICATION_CONFIRMATION = "application_confirmation"
    APPLICATION_RECEIVED = "application_received"
    UNDER_REVIEW = "under_review"
    INTERVIEW_INVITATION = "interview_invitation"
    ASSESSMENT_INVITATION = "assessment_invitation"
    REJECTION = "rejection"
    JOB_OFFER = "job_offer"
    OTHER_JOB_RELATED = "other_job_related"
    NOT_JOB_RELATED = "not_job_related"


CATEGORY_LABELS = {
    "application_confirmation": "Application confirmation", "application_received": "Application received",
    "under_review": "Under review", "interview_invitation": "Interview invitation",
    "assessment_invitation": "Assessment invitation", "rejection": "Rejection", "job_offer": "Job offer",
    "other_job_related": "Other job-related", "not_job_related": "Not job related",
}


class ProcessingStatus(str, Enum):
    MATCHED = "matched"
    NEEDS_REVIEW = "needs_review"
    IGNORED = "ignored"


class ChangeSource(str, Enum):
    MANUAL = "manual"
    GMAIL = "gmail"
    SYSTEM = "system"


class SyncStatus(str, Enum):
    IDLE = "idle"
    SYNCING = "syncing"
    ERROR = "error"
    REVOKED = "revoked"
