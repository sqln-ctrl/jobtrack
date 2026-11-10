from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ApplicationStatus, EmploymentType


class PlatformOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    is_default: bool


class PlatformIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip()


class ApplicationBase(BaseModel):
    job_title: str = Field(min_length=1, max_length=255)
    company_name: str = Field(min_length=1, max_length=255)
    platform_id: int
    application_date: date
    status: ApplicationStatus = ApplicationStatus.APPLIED
    job_description: Optional[str] = None
    job_url: Optional[str] = Field(default=None, max_length=2048)
    company_website: Optional[str] = Field(default=None, max_length=2048)
    location: Optional[str] = Field(default=None, max_length=255)
    employment_type: Optional[EmploymentType] = None
    salary_range: Optional[str] = Field(default=None, max_length=120)
    notes: Optional[str] = None
    contact_person: Optional[str] = Field(default=None, max_length=255)

    @field_validator("job_title", "company_name", mode="before")
    @classmethod
    def strip_required(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator(
        "job_description", "job_url", "company_website", "location", "employment_type",
        "salary_range", "notes", "contact_person", mode="before",
    )
    @classmethod
    def blank_to_none(cls, v):
        return None if isinstance(v, str) and not v.strip() else v


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(ApplicationBase):
    pass


class StatusUpdate(BaseModel):
    status: ApplicationStatus
    note: Optional[str] = Field(default=None, max_length=500)


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    job_title: str
    company_name: str
    platform_id: int
    platform: PlatformOut
    application_date: date
    status: ApplicationStatus
    job_description: Optional[str]
    job_url: Optional[str]
    company_website: Optional[str]
    location: Optional[str]
    employment_type: Optional[EmploymentType]
    salary_range: Optional[str]
    notes: Optional[str]
    contact_person: Optional[str]
    created_at: datetime
    updated_at: datetime


class ApplicationPage(BaseModel):
    items: List[ApplicationOut]
    total: int
    page: int
    page_size: int


class TimelineEvent(BaseModel):
    kind: str  # submitted | status | email | interview
    at: datetime
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
