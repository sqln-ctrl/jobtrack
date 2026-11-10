from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ApplicationRef(BaseModel):
    id: int
    job_title: str
    company_name: str
    confidence: float


class EmailOut(BaseModel):
    id: int
    sender: str
    subject: str
    excerpt: Optional[str]
    received_at: datetime
    classification: str
    classification_label: str
    classification_confidence: float
    extracted_company: Optional[str]
    extracted_job_title: Optional[str]
    processing_status: str
    applications: List[ApplicationRef]


class EmailPage(BaseModel):
    items: List[EmailOut]
    total: int
    page: int
    page_size: int


class MatchRequest(BaseModel):
    application_id: int
