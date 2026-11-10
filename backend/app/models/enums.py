from enum import Enum


class ApplicationStatus(str, Enum):
    SAVED = "saved"
    APPLIED = "applied"
    UNDER_REVIEW = "under_review"
    INTERVIEW = "interview"
    ASSESSMENT = "assessment"
    REJECTED = "rejected"
    OFFER = "offer"
    WITHDRAWN = "withdrawn"
    NO_RESPONSE = "no_response"


STATUS_LABELS = {
    "saved": "Saved", "applied": "Applied", "under_review": "Under review", "interview": "Interview",
    "assessment": "Assessment", "rejected": "Rejected", "offer": "Offer", "withdrawn": "Withdrawn",
    "no_response": "No response",
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
