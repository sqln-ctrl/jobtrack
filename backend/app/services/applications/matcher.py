"""Match a classified email to one of the user's applications.

Scoring (highest applicable wins):
  0.95  the application's job URL appears in the email, or exact job title + company
  0.80  company + related job title
  0.65  company found in the sender name/domain only
  0.55  company found only in the text

Every credible candidate is linked automatically. When more than one application has the
same score, the most recently submitted application wins so matching is deterministic.
Emails with no candidate remain unmatched and are retried after later Gmail syncs.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from app.email_text import norm
from app.models.application import JobApplication
from app.services.email_classifier.extractor import Extracted, sender_parts

THRESHOLD = 0.55

STOP = {"the", "a", "an", "and", "of", "for", "at", "with", "in", "to"}
LEGAL = {"inc", "llc", "ltd", "limited", "pvt", "private", "corp", "corporation", "co", "plc", "gmbh"}
GENERIC_CO = {"technologies", "technology", "tech", "solutions", "systems", "software", "group", "labs", "services", "studio", "studios", "consulting", "digital"}


@dataclass
class MatchResult:
    application: Optional[JobApplication]
    confidence: float
    ambiguous: bool = False
    candidates: List[Tuple[JobApplication, float]] = field(default_factory=list)


def company_core(name: str) -> str:
    toks = [t for t in norm(name).split() if t not in LEGAL]
    core = [t for t in toks if t not in GENERIC_CO] or toks
    return " ".join(core)


def _tokens(title: str) -> List[str]:
    return [t for t in norm(title).split() if t not in STOP]


def _norm_url(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url.strip().lower()).split("?")[0].rstrip("/")


def _company_hit(core: str, sender_name: str, domain: str, text: str) -> Optional[str]:
    if len(core) < 2:
        return None
    nospace = core.replace(" ", "")
    pattern = rf"\b{re.escape(core)}\b"
    if re.search(pattern, sender_name) or (domain and (domain == nospace or (len(nospace) >= 4 and nospace in domain))):
        return "sender"
    if len(core) >= 3 and re.search(pattern, text):
        return "text"
    return None


def _title_match(app_title: str, headline: str, body: str) -> Optional[str]:
    phrase = " ".join(_tokens(app_title))
    if not phrase:
        return None
    head = " ".join(_tokens(headline))
    if re.search(rf"\b{re.escape(phrase)}\b", head):
        return "exact"
    wanted = set(phrase.split())
    if len(wanted & set(head.split())) / len(wanted) >= 0.6 or re.search(rf"\b{re.escape(phrase)}\b", " ".join(_tokens(body))):
        return "related"
    return None


def match_application(
    applications: Sequence[JobApplication], *, sender: str, subject: str, body: str, extracted: Extracted
) -> MatchResult:
    name, _, domain = sender_parts(sender)
    sender_name = norm(name)
    text = norm(f"{subject} {body}")
    raw_text = f"{subject} {body}".lower()
    headline = f"{subject} {extracted.job_title or ''}"
    scored: List[Tuple[JobApplication, float]] = []

    for app in applications:
        score = 0.0
        if app.job_url and len(_norm_url(app.job_url)) > 12 and _norm_url(app.job_url) in raw_text:
            score = 0.95
        else:
            hit = _company_hit(company_core(app.company_name), sender_name, domain, text)
            if hit:
                title = _title_match(app.job_title, headline, body)
                score = 0.95 if title == "exact" else 0.8 if title == "related" else 0.65 if hit == "sender" else 0.55
        if score > 0:
            scored.append((app, score))

    # A title/company signal takes priority. For equally likely candidates, prefer the
    # newest application rather than requiring the user to resolve a manual queue.
    scored.sort(key=lambda pair: (pair[1], pair[0].application_date, pair[0].id), reverse=True)
    if not scored:
        return MatchResult(None, 0.0)
    top_app, top = scored[0]
    if top < THRESHOLD:
        return MatchResult(None, top, False, scored)
    return MatchResult(top_app, top, False, scored)
