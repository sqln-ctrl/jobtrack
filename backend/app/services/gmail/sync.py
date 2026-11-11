import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import Conflict, NotFound
from app.models.application import JobApplication
from app.models.email import Email
from app.models.enums import EmailCategory, ProcessingStatus, SyncStatus
from app.models.gmail import GmailConnection
from app.services import job_alerts
from app.services.applications.email_linking import link_email
from app.services.applications.matcher import match_application
from app.services.email_classifier.classifier import EmailClassifier, RuleBasedClassifier
from app.services.email_classifier.extractor import extract
from app.services.gmail.client import GmailAuthError, GmailClient, GmailError, HistoryExpired, ParsedMessage, parse_message
from app.services.gmail.tokens import get_valid_access_token

log = logging.getLogger(__name__)

JOB_QUERY = (
    '(application OR applied OR applying OR interview OR assessment OR offer OR candidate OR candidacy '
    'OR recruiter OR "hiring team" OR position OR "thank you for your interest") '
    '-in:chats -category:promotions -category:social'
)
LINKEDIN_ALERT_QUERY = 'from:(jobalerts-noreply@linkedin.com OR jobs-noreply@linkedin.com) ("job alert" OR "jobs for you" OR "new jobs")'
STALE_SYNC = timedelta(minutes=10)


@dataclass
class SyncResult:
    fetched: int = 0
    stored: int = 0
    matched: int = 0
    needs_review: int = 0
    skipped: int = 0
    job_alerts: int = 0


def begin_sync(db: Session, user_id: int) -> GmailConnection:
    """Mark a sync as started, refusing to run two at once."""
    conn = db.scalar(select(GmailConnection).where(GmailConnection.user_id == user_id))
    if conn is None:
        raise NotFound("Gmail is not connected")
    started = conn.sync_started_at
    if started is not None and started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    if conn.sync_status == SyncStatus.SYNCING.value and started and datetime.now(timezone.utc) - started < STALE_SYNC:
        raise Conflict("A sync is already running")
    conn.sync_status = SyncStatus.SYNCING.value
    conn.sync_started_at = datetime.now(timezone.utc)
    db.commit()
    return conn


class GmailSyncService:
    def __init__(
        self, db: Session, client_factory: Callable[[str], GmailClient] = GmailClient,
        token_provider: Callable = get_valid_access_token, classifier: Optional[EmailClassifier] = None,
    ):
        self.db = db
        self.client_factory = client_factory
        self.token_provider = token_provider
        self.classifier = classifier or RuleBasedClassifier()

    def sync_user(self, user_id: int) -> SyncResult:
        conn = self.db.scalar(select(GmailConnection).where(GmailConnection.user_id == user_id))
        if conn is None:
            raise NotFound("Gmail is not connected")
        result = SyncResult()
        try:
            client = self.client_factory(self.token_provider(self.db, conn))
            latest_history_id = str(client.profile().get("historyId", ""))
            ids = self._collect_ids(client, conn)
            result.fetched = len(ids)
            self._process_ids(client, conn.user_id, ids, result)

            conn.history_id = latest_history_id or conn.history_id
            conn.last_synced_at = datetime.now(timezone.utc)
            conn.sync_status = SyncStatus.IDLE.value
            conn.last_error = None
        except GmailAuthError:
            self.db.rollback()
            conn = self.db.get(GmailConnection, conn.id)
            conn.sync_status = SyncStatus.REVOKED.value
            conn.last_error = "Gmail access expired or was revoked. Reconnect Gmail to resume syncing."
        except Exception as exc:  # never log email content, only the error type
            log.error("Gmail sync failed for user %s: %s", user_id, type(exc).__name__)
            self.db.rollback()
            conn = self.db.get(GmailConnection, conn.id)
            conn.sync_status = SyncStatus.ERROR.value
            conn.last_error = f"Sync failed ({type(exc).__name__}). Try again in a few minutes."
        self.db.commit()
        return result

    def _collect_ids(self, client: GmailClient, conn: GmailConnection) -> List[str]:
        s = get_settings()
        alert_query = f"{LINKEDIN_ALERT_QUERY} newer_than:{s.gmail_sync_days}d"
        if conn.history_id:
            try:
                # History only covers mail that arrived since the last sync. Re-run the
                # bounded LinkedIn query as well so existing Gmail connections receive
                # their recent alerts when this feature is first introduced.
                changed_ids = client.history_message_ids(conn.history_id)
                alert_ids = client.list_message_ids(alert_query, s.gmail_max_messages_per_sync)
                return list(dict.fromkeys(changed_ids + alert_ids))
            except HistoryExpired:
                pass  # fall through to a fresh full sync
        query = f"{JOB_QUERY} newer_than:{s.gmail_sync_days}d"
        application_ids = client.list_message_ids(query, s.gmail_max_messages_per_sync)
        alert_ids = client.list_message_ids(alert_query, s.gmail_max_messages_per_sync)
        return list(dict.fromkeys(application_ids + alert_ids))

    def _process_ids(self, client: GmailClient, user_id: int, ids: List[str], result: SyncResult) -> None:
        known = set(self.db.scalars(select(Email.gmail_message_id).where(Email.user_id == user_id, Email.gmail_message_id.in_(ids)))) if ids else set()
        known |= job_alerts.message_ids(self.db, user_id)
        parsed: List[ParsedMessage] = []
        for mid in ids:
            if mid in known:
                continue
            raw = client.get_message(mid)
            if raw:
                parsed.append(parse_message(raw))
        parsed.sort(key=lambda m: m.received_at)  # oldest first so status changes replay in order

        apps = list(self.db.scalars(select(JobApplication).where(JobApplication.user_id == user_id)))
        for message in parsed:
            try:
                self._process_message(user_id, message, apps, result)
                self.db.commit()
            except IntegrityError:  # same message processed concurrently
                self.db.rollback()

    def _process_message(self, user_id: int, m: ParsedMessage, apps: List[JobApplication], result: SyncResult) -> None:
        if job_alerts.is_linkedin_job_alert(m.sender, m.subject):
            listings = job_alerts.extract_linkedin_listings(m.html_body)
            if listings:
                result.job_alerts += job_alerts.store_listings(self.db, user_id, m, listings)
                return
        cls = self.classifier.classify(m.sender, m.subject, m.body)
        if cls.category == EmailCategory.NOT_JOB_RELATED:
            result.skipped += 1  # unrelated mail is never stored
            return
        extracted = extract(m.sender, m.subject, m.body)
        email = Email(
            user_id=user_id, gmail_message_id=m.id, gmail_thread_id=m.thread_id, sender=m.sender[:512], subject=m.subject[:998],
            email_body_excerpt=m.body[:1500], received_at=m.received_at, classification=cls.category.value,
            classification_confidence=cls.confidence, extracted_company=extracted.company, extracted_job_title=extracted.job_title,
            processing_status=ProcessingStatus.NEEDS_REVIEW.value,
        )
        self.db.add(email)
        self.db.flush()
        result.stored += 1

        match = match_application(apps, sender=m.sender, subject=m.subject, body=m.body, extracted=extracted)
        if match.application is not None:
            link_email(self.db, email, match.application, match.confidence)
            result.matched += 1
        else:
            result.needs_review += 1


def run_sync_in_background(user_id: int) -> None:
    """Entry point for FastAPI background tasks: owns its own DB session."""
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        GmailSyncService(db).sync_user(user_id)
