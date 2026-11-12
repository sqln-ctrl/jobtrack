"""Extraction and read APIs for LinkedIn job-alert email recommendations."""
import html
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.job_alert import JobAlert
from app.schemas.job_alert import JobAlertOut


LINKEDIN_SENDER = re.compile(r"@(?:[\w-]+\.)?linkedin\.com(?:>|$)", re.I)
ALERT_SUBJECT = re.compile(r"\b(job alert|jobs? for you|new jobs?|recommended jobs?)\b", re.I)
ANCHOR = re.compile(r"<a\b[^>]*?href\s*=\s*(['\"])(.*?)\1[^>]*>(.*?)</a\s*>", re.I | re.S)
TAG = re.compile(r"(?s)<[^>]+>")
SPACE = re.compile(r"\s+")
GENERIC_LINK_TEXT = re.compile(r"^(apply|apply now|view job|view|learn more|see job|linkedin)$", re.I)
MAX_ALERT_AGE = timedelta(days=7)


@dataclass(frozen=True)
class AlertListing:
    job_title: str
    company_name: Optional[str]
    location: Optional[str]
    description: Optional[str]
    job_url: str


def is_linkedin_job_alert(sender: str, subject: str) -> bool:
    return bool(LINKEDIN_SENDER.search(sender or "") and ALERT_SUBJECT.search(subject or ""))


def is_recent(received_at: datetime) -> bool:
    if received_at.tzinfo is None:
        received_at = received_at.replace(tzinfo=timezone.utc)
    return received_at >= datetime.now(timezone.utc) - MAX_ALERT_AGE


def _text(value: str) -> str:
    return SPACE.sub(" ", html.unescape(TAG.sub(" ", value or ""))).strip()


def _is_job_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower().endswith("linkedin.com") and "/jobs/" in parsed.path


def _title_and_company(label: str) -> Tuple[str, Optional[str]]:
    label = _text(label)
    if not label or GENERIC_LINK_TEXT.match(label):
        return "Job on LinkedIn", None
    # LinkedIn occasionally puts both values in the link label.
    parts = re.split(r"\s+(?:at|[-â€”])\s+", label, maxsplit=1, flags=re.I)
    return parts[0][:255], (parts[1][:255] if len(parts) == 2 else None)


def _description(card_html: str) -> Optional[str]:
    """Keep a compact, readable excerpt from the remainder of a LinkedIn job card."""
    value = _text(card_html)
    value = re.sub(r"\b(?:apply(?: now)?|view job|learn more|see job)\b", "", value, flags=re.I)
    value = SPACE.sub(" ", value).strip(" -|·")
    return value[:360] or None


def extract_linkedin_listings(html_body: str) -> List[AlertListing]:
    """Return job-view links and their labels from a LinkedIn email's HTML body.

    The HTML layout varies across LinkedIn templates, so the stable contract we
    rely on is the job-view URL. Company and location are optional enrichment.
    """
    listings, seen = [], set()
    links = list(ANCHOR.finditer(html_body or ""))
    for index, match in enumerate(links):
        raw_url, label = match.group(2), match.group(3)
        url = html.unescape(raw_url).strip()
        if not _is_job_url(url) or url in seen:
            continue
        seen.add(url)
        title, company = _title_and_company(label)
        next_start = links[index + 1].start() if index + 1 < len(links) else min(len(html_body), match.end() + 1200)
        description = _description(html_body[match.end():next_start])
        listings.append(AlertListing(title, company, None, description, url[:2048]))
    return listings


def message_ids(db: Session, user_id: int) -> set[str]:
    return set(db.scalars(select(JobAlert.gmail_message_id).where(JobAlert.user_id == user_id)))


def store_listings(db: Session, user_id: int, message, listings: List[AlertListing]) -> int:
    for position, listing in enumerate(listings):
        db.add(JobAlert(
            user_id=user_id, gmail_message_id=message.id, gmail_thread_id=message.thread_id or None,
            position=position, job_title=listing.job_title, company_name=listing.company_name,
            location=listing.location, description=listing.description, job_url=listing.job_url, received_at=message.received_at,
        ))
    return len(listings)


def list_alerts(db: Session, user_id: int, page: int, page_size: int) -> Tuple[List[JobAlert], int]:
    cutoff = datetime.now(timezone.utc) - MAX_ALERT_AGE
    stmt = select(JobAlert).where(JobAlert.user_id == user_id, JobAlert.received_at >= cutoff)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(JobAlert.received_at.desc(), JobAlert.position).offset((page - 1) * page_size).limit(page_size)).all()
    return list(rows), total


def alert_to_out(alert: JobAlert) -> JobAlertOut:
    return JobAlertOut(
        id=alert.id, job_title=alert.job_title, company_name=alert.company_name,
        location=alert.location, description=alert.description, job_url=alert.job_url, received_at=alert.received_at,
    )
