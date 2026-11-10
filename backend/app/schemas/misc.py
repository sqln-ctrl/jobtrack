from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.application import TimelineEvent
from app.schemas.email import EmailOut
from app.schemas.application import ApplicationOut


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    profile_picture: Optional[str]


class MeOut(BaseModel):
    user: UserOut
    gmail_connected: bool


class GmailStatus(BaseModel):
    connected: bool
    gmail_email: Optional[str] = None
    sync_status: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    last_error: Optional[str] = None


class InterviewIn(BaseModel):
    application_id: int
    interview_date: datetime
    interview_type: Optional[str] = Field(default=None, max_length=64)
    meeting_link: Optional[str] = Field(default=None, max_length=2048)
    notes: Optional[str] = None


class InterviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    interview_date: datetime
    interview_type: Optional[str]
    meeting_link: Optional[str]
    notes: Optional[str]
    job_title: str = ""
    company_name: str = ""


class ApplicationDetail(BaseModel):
    application: ApplicationOut
    timeline: List[TimelineEvent]
    emails: List[EmailOut]
    interviews: List[InterviewOut]
