from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class JobAlertOut(BaseModel):
    id: int
    job_title: str
    company_name: Optional[str]
    location: Optional[str]
    job_url: str
    received_at: datetime


class JobAlertPage(BaseModel):
    items: List[JobAlertOut]
    total: int
    page: int
    page_size: int
