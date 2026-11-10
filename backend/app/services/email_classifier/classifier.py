"""Rule-based email classifier.

The `EmailClassifier` protocol is the seam for a future LLM-based classifier:
anything with a matching `classify` method can be swapped in.
"""
import re
from dataclasses import dataclass
from typing import Protocol

from app.models.enums import EmailCategory as C


@dataclass(frozen=True)
class Classification:
    category: C
    confidence: float
    signals: tuple = ()


class EmailClassifier(Protocol):
    def classify(self, sender: str, subject: str, body: str) -> Classification: ...


def _rx(*patterns):
    return [re.compile(p, re.I | re.S) for p in patterns]


NOISE = _rx(
    r"job alerts?\b", r"jobs? (you may|for you|similar to|matching)", r"recommended jobs?",
    r"new jobs? (for|matching|in)\b", r"\bnewsletter\b", r"people (also )?viewed", r"\bjobs? digest\b",
)

# Order matters: the first category with a hit wins. Rejections and offers are checked before
# interviews because their text often mentions interviews ("we enjoyed interviewing you").
RULES = [
    (C.REJECTION, _rx(
        r"\bunfortunately\b.{0,120}\b(not|unable|decided|other candidates|move forward|pursue|proceed)",
        r"(regret|sorry) to (inform|tell|let) you",
        r"not (be )?(moving|move|proceeding|proceed) forward",
        r"(move|moving|go|going|proceed|proceeding|pursue|pursuing)( forward)?( with)? (other|another|different) (candidates?|applicants?|applications?)",
        r"position (has been|was|is) (now )?(filled|closed)",
        r"(not|haven't|have not) been selected",
        r"we (are )?unable to (offer|move|proceed)",
        r"will not be (moving|proceeding|taking)",
    )),
    (C.JOB_OFFER, _rx(
        r"pleased to (offer|extend)", r"\b(job|employment) offer\b", r"\boffer letter\b",
        r"(extend|extending) (you )?an offer", r"excited to offer", r"offer of employment", r"\bofficial offer\b",
    )),
    (C.INTERVIEW_INVITATION, _rx(
        r"interview invitation", r"invit\w+ (you )?(to|for) (an? )?(\w+ )?interview",
        r"schedul\w+ (an? |your )?(\w+ )?interview", r"(phone|video|technical|onsite|on-site|panel|final)[- ]?(screen|interview)",
        r"like to (interview|speak with|chat with|meet with) you", r"interview (is )?(scheduled|confirmed)",
        r"selected you for an interview", r"availability for (a |an )?(call|interview|chat)",
    )),
    (C.ASSESSMENT_INVITATION, _rx(
        r"(coding|technical|skills?|online|take[- ]home) (assessment|challenge|test|assignment)",
        r"\b(hackerrank|codility|codesignal|testgorilla|coderbyte)\b",
        r"complete (the |a |an |this )?(following )?(assessment|challenge|assignment)",
    )),
    (C.UNDER_REVIEW, _rx(
        r"(application|resume|cv|profile|candidacy)[^.\n]{0,40}(under review|being reviewed|in review|being considered)",
        r"reviewing your (application|resume|cv|profile)",
    )),
    (C.APPLICATION_CONFIRMATION, _rx(
        r"thank(s| you) for (applying|your application|your interest in)",
        r"successfully (applied|submitted)", r"you (have )?applied (to|for)", r"application (was )?(submitted|sent)\b",
    )),
    (C.APPLICATION_RECEIVED, _rx(
        r"(we('ve| have) )?received your application", r"application (has been )?received",
    )),
]

GENERIC = _rx(r"\byour application\b", r"\brecruiter\b", r"\bhiring (manager|team)\b", r"\bjob (opening|opportunity|application)\b", r"\bcandidacy\b", r"\bapplicant\b")
JOB_WORDS = re.compile(r"\b(application|applied|applying|applicant|candidate|candidacy|position|role|interview|recruit\w*|hiring|job|career|resume|cv)\b", re.I)


class RuleBasedClassifier:
    def classify(self, sender: str, subject: str, body: str) -> Classification:
        subject = subject or ""
        body = (body or "")[:4000]
        if any(p.search(subject) for p in NOISE):
            return Classification(C.NOT_JOB_RELATED, 0.9, ("job-alert",))

        # Pass 1: subject lines are strong signals. Pass 2: body, gated on job context so that
        # promotional mail containing phrases like "unfortunately" is not misread as a rejection.
        context_words = {m.group(1).lower() for m in JOB_WORDS.finditer(subject + " " + body)}
        has_context = len(context_words) >= 2 or bool(JOB_WORDS.search(subject))
        for text, base, gated in ((subject, 0.9, False), (body, 0.75, True)):
            if gated and not has_context:
                continue
            for category, patterns in RULES:
                hits = [p.pattern for p in patterns if p.search(text)]
                if hits:
                    return Classification(category, min(0.97, base + 0.03 * (len(hits) - 1)), tuple(hits[:3]))

        if has_context and any(p.search(subject + " " + body) for p in GENERIC):
            return Classification(C.OTHER_JOB_RELATED, 0.5, ("generic",))
        return Classification(C.NOT_JOB_RELATED, 0.8)
