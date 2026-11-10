from datetime import date, datetime, timezone

from sqlalchemy import select

from app.models import ApplicationHistory, Email, GmailConnection, JobApplication, Platform
from app.core.security import encrypt
from app.services.applications.matcher import match_application
from app.services.email_classifier.extractor import extract
from app.services.gmail.sync import GmailSyncService
from tests.conftest import make_user


def add_app(db, user, title, company, status="applied", url=None):
    p = db.scalar(select(Platform).where(Platform.name == "LinkedIn"))
    a = JobApplication(user_id=user.id, platform_id=p.id, job_title=title, company_name=company, application_date=date(2026, 11, 1), status=status, job_url=url)
    db.add(a)
    db.commit()
    return a


def match(apps, sender, subject, body=""):
    return match_application(apps, sender=sender, subject=subject, body=body, extracted=extract(sender, subject, body))


def test_exact_title_and_company(db, user):
    a = add_app(db, user, "Backend Developer", "ABC Technologies")
    b = add_app(db, user, "Frontend Developer", "ABC Technologies")
    r = match([a, b], "ABC Recruiting <jobs@abc.com>", "Your application for Backend Developer at ABC Technologies")
    assert r.application is a and r.confidence >= 0.95


def test_two_roles_same_company_is_ambiguous(db, user):
    a = add_app(db, user, "Backend Developer", "ABC")
    b = add_app(db, user, "Data Engineer", "ABC")
    r = match([a, b], "ABC <hr@abc.com>", "An update on your application")
    assert r.application is None and r.ambiguous


def test_company_only_in_text_is_not_auto_matched(db, user):
    a = add_app(db, user, "Backend Developer", "Globex")
    r = match([a], "recruiter@staffing-agency.com", "Hello", "I am reaching out about a role at Globex")
    assert r.application is None


def test_job_url_match(db, user):
    a = add_app(db, user, "Engineer", "Initech", url="https://initech.com/careers/123")
    r = match([a], "noreply@ats.io", "Update", "See https://initech.com/careers/123?src=mail for details")
    assert r.application is a


class FakeClient:
    def __init__(self, messages, history_expired=False):
        self.messages, self.history_expired, self.fetched = messages, history_expired, []

    def profile(self):
        return {"historyId": "999"}

    def list_message_ids(self, query, limit):
        return list(self.messages)

    def history_message_ids(self, start):
        from app.services.gmail.client import HistoryExpired
        if self.history_expired:
            raise HistoryExpired()
        return []

    def get_message(self, mid):
        self.fetched.append(mid)
        return self.messages[mid]


def raw(mid, sender, subject, body, ts):
    import base64
    data = base64.urlsafe_b64encode(body.encode()).decode()
    return {"id": mid, "threadId": "t" + mid, "internalDate": str(ts * 1000), "payload": {
        "mimeType": "text/plain", "body": {"data": data}, "headers": [{"name": "From", "value": sender}, {"name": "Subject", "value": subject}]}}


def connect(db, user, history_id=None):
    conn = GmailConnection(user_id=user.id, gmail_email=user.email, encrypted_access_token=encrypt("a"), encrypted_refresh_token=encrypt("r"), history_id=history_id)
    db.add(conn)
    db.commit()
    return conn


def run(db, user, client):
    return GmailSyncService(db, client_factory=lambda _t: client, token_provider=lambda *_: "tok").sync_user(user.id)


def test_sync_updates_status_in_order_and_records_history(db, user):
    app = add_app(db, user, "Backend Developer", "ABC Technologies")
    conn = connect(db, user)
    msgs = {
        # deliberately listed newest-first, as Gmail does
        "m3": raw("m3", "ABC Recruiting <jobs@abc.com>", "Interview Invitation — Backend Developer", "We would like to invite you to an interview for Backend Developer at ABC Technologies.", 1_800_000_300),
        "m2": raw("m2", "ABC Recruiting <jobs@abc.com>", "Your application is under review", "Our hiring team is reviewing your application for Backend Developer at ABC Technologies.", 1_800_000_200),
        "m1": raw("m1", "ABC Recruiting <jobs@abc.com>", "Your application for Backend Developer at ABC Technologies", "Thank you for applying.", 1_800_000_100),
        "spam": raw("spam", "deals@shop.com", "50% off", "Big sale this weekend", 1_800_000_400),
    }
    result = run(db, user, FakeClient(msgs))
    assert (result.stored, result.matched, result.skipped) == (3, 3, 1)
    db.refresh(app)
    assert app.status == "interview"
    steps = [(h.previous_status, h.new_status, h.change_source) for h in db.scalars(select(ApplicationHistory).where(ApplicationHistory.application_id == app.id))]
    assert ("applied", "under_review", "gmail") in steps and ("under_review", "interview", "gmail") in steps
    db.refresh(conn)
    assert conn.history_id == "999" and conn.sync_status == "idle" and conn.last_synced_at is not None


def test_sync_is_idempotent_and_never_downgrades(db, user):
    app = add_app(db, user, "Backend Developer", "ABC", status="rejected")
    connect(db, user)
    msgs = {"m1": raw("m1", "ABC <hr@abc.com>", "Interview Invitation — Backend Developer", "Please schedule an interview.", 1_800_000_100)}
    run(db, user, FakeClient(msgs))
    run(db, user, FakeClient(msgs))
    assert db.query(Email).count() == 1
    db.refresh(app)
    assert app.status == "rejected"  # a final outcome is never overwritten by an email


def test_ambiguous_email_goes_to_review_without_touching_applications(db, user):
    a = add_app(db, user, "Backend Developer", "ABC")
    b = add_app(db, user, "Data Engineer", "ABC")
    connect(db, user)
    run(db, user, FakeClient({"m1": raw("m1", "ABC <hr@abc.com>", "Update on your application", "Unfortunately we will not be moving forward.", 1_800_000_100)}))
    email = db.scalar(select(Email))
    assert email.processing_status == "needs_review"
    db.refresh(a), db.refresh(b)
    assert a.status == b.status == "applied"


def test_expired_history_falls_back_to_full_sync(db, user):
    add_app(db, user, "Backend Developer", "ABC")
    connect(db, user, history_id="1")
    msgs = {"m1": raw("m1", "ABC <hr@abc.com>", "Application received", "We received your application for Backend Developer at ABC.", 1_800_000_100)}
    result = run(db, user, FakeClient(msgs, history_expired=True))
    assert result.stored == 1


def test_auth_failure_marks_connection_revoked(db, user):
    from app.services.gmail.client import GmailAuthError
    conn = connect(db, user)

    def boom(*_):
        raise GmailAuthError("nope")
    GmailSyncService(db, client_factory=lambda t: None, token_provider=boom).sync_user(user.id)
    db.refresh(conn)
    assert conn.sync_status == "revoked"


def test_other_users_applications_are_never_matched(db, user):
    other = make_user(db, 2)
    add_app(db, other, "Backend Developer", "ABC")
    connect(db, user)
    run(db, user, FakeClient({"m1": raw("m1", "ABC <hr@abc.com>", "Interview Invitation — Backend Developer", "Please schedule an interview.", 1_800_000_100)}))
    assert db.scalar(select(Email)).processing_status == "needs_review"
    assert db.scalar(select(JobApplication).where(JobApplication.user_id == other.id)).status == "applied"
