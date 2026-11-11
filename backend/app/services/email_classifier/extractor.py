"""Pull a company name and job title out of an email."""
import re
from dataclasses import dataclass
from email.utils import parseaddr
from typing import Optional, Tuple

_SEP = r"[|\-—–:!\.]"
SUBJECT_PATTERNS = [re.compile(p, re.I) for p in (
    rf"application (?:for|to) (?:the )?(?P<title>.{{2,100}}?)\s+(?:position |role )?(?:at|with|@)\s+(?P<company>[^|\-—–:!\.]{{2,80}})",
    rf"application (?:was )?(?:sent|submitted) to (?P<company>[^|\-—–:!\.]{{2,80}})",
    rf"(?:applying|applied|application) (?:to|at|with) (?P<company>[^|\-—–:!\.]{{2,80}})",
    rf"(?P<title>[^|\-—–:]{{2,100}}?) (?:position|role|opportunity) (?:at|with) (?P<company>[^|\-—–:!\.]{{2,80}})",
    rf"(?:interview|assessment|offer|invitation|application|update)[^|\-—–:]*[\-—–|:]\s*(?P<title>[^|\-—–:]{{2,100}}?)(?:\s+(?:at|with)\s+(?P<company>[^|\-—–:!\.]{{2,80}}))?\s*$",
)]
BODY_PATTERNS = [re.compile(p, re.I) for p in (
    r"(?:position|role|job) (?:of |as )?(?:the )?[\"“']?(?P<title>[^\"”'\n\.,]{3,80}?)[\"”']? (?:at|with) (?P<company>[^\.\n,!;]{2,60})",
    r"(?:applying|applied|application) (?:for|to) (?:the )?[\"“']?(?P<title>[^\"”'\n\.,]{3,80}?)[\"”']?(?: position| role)? (?:at|with) (?P<company>[^\.\n,!;]{2,60})",
)]
LINKEDIN_SENT = re.compile(r"your application was sent to\s+", re.I)
SENDER_NOISE = re.compile(r"\b(recruiting|recruitment|recruiter|careers?|talent( acquisition)?|hr|human resources|jobs|hiring|team|no[- ]?reply|notifications?|noreply|people|staffing)\b", re.I)
GENERIC_DOMAINS = {"gmail", "googlemail", "yahoo", "outlook", "hotmail", "icloud", "proton", "protonmail", "live", "aol"}
ATS_DOMAINS = {
    "greenhouse", "greenhouse-mail", "lever", "workday", "myworkday", "myworkdayjobs", "smartrecruiters", "icims", "taleo",
    "ashbyhq", "bamboohr", "jobvite", "successfactors", "linkedin", "indeed", "glassdoor", "rozee", "workable",
    "recruitee", "breezy", "jazzhr", "applytojob", "teamtailor", "mail", "email", "notifications",
}
TLD_PARTS = {"com", "co", "org", "net", "io", "pk", "uk", "ai", "dev", "app", "us", "in", "ae"}


@dataclass(frozen=True)
class Extracted:
    company: Optional[str] = None
    job_title: Optional[str] = None


def sender_parts(sender: str) -> Tuple[str, str, str]:
    """Return (display name, address, second-level domain label)."""
    name, addr = parseaddr(sender or "")
    domain = addr.split("@", 1)[1].lower() if "@" in addr else ""
    labels = [p for p in domain.split(".") if p]
    while labels and labels[-1] in TLD_PARTS and len(labels) > 1:
        labels.pop()
    return name.strip(), addr, (labels[-1] if labels else "")


def _clean(value: Optional[str], limit: int = 120) -> Optional[str]:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip(" \t\"'“”.,;:-—–")
    value = re.sub(r"\s+(position|role|team|opportunity)$", "", value, flags=re.I)
    return value[:limit] if len(value) >= 2 else None


def _from_patterns(patterns, text):
    for pattern in patterns:
        m = pattern.search(text)
        if m:
            g = m.groupdict()
            return _clean(g.get("title")), _clean(g.get("company"), 80)
    return None, None


def _linkedin_confirmation_title(body: str, company: Optional[str]) -> Optional[str]:
    """Extract a title from LinkedIn's confirmation-card layout.

    Example: "sent to Acme Backend Engineer (Remote) Acme Pakistan View job".
    The repeated company name gives us a dependable boundary for the job title.
    """
    if not company:
        return None
    marker = LINKEDIN_SENT.search(body or "")
    if not marker:
        return None
    tail = (body or "")[marker.end():]
    end = re.search(r"\s+view job\b", tail, re.I)
    if not end:
        return None
    card = tail[:end.start()].strip()
    if not card.lower().startswith(company.lower()):
        return None
    remainder = card[len(company):].strip()
    repeated_company = remainder.lower().find(company.lower())
    if repeated_company <= 0:
        return None
    return _clean(remainder[:repeated_company])


def extract(sender: str, subject: str, body: str) -> Extracted:
    title, company = _from_patterns(SUBJECT_PATTERNS, subject or "")
    if not (title and company):
        b_title, b_company = _from_patterns(BODY_PATTERNS, (body or "")[:3000])
        title, company = title or b_title, company or b_company
    if not company:
        name, _, label = sender_parts(sender)
        cleaned = _clean(SENDER_NOISE.sub(" ", name))
        if cleaned:
            company = cleaned
        elif label and label not in GENERIC_DOMAINS and label not in ATS_DOMAINS:
            company = label.title()
    if not title:
        title = _linkedin_confirmation_title(body or "", company)
    return Extracted(company=company, job_title=title)
