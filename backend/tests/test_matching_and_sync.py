from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.models import ApplicationEmail, ApplicationHistory, Email, GmailConnection, JobAlert, JobApplication, Platform
from app.core.security import encrypt
from app.services.applications.matcher import match_application
from app.services.email_classifier.extractor import extract
from app.services.gmail.sync import GmailSyncService
from app.services import job_alerts as job_alert_service
from tests.conftest import make_user


def add_app(db, user, title, company, status="sent", url=None):
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


def test_two_roles_same_company_auto_matches_the_most_recent_application(db, user):
    a = add_app(db, user, "Backend Developer", "ABC")
    b = add_app(db, user, "Data Engineer", "ABC")
    r = match([a, b], "ABC <hr@abc.com>", "An update on your application")
    assert r.application is b and not r.ambiguous


def test_company_only_in_text_is_auto_matched(db, user):
    a = add_app(db, user, "Backend Developer", "Globex")
    r = match([a], "recruiter@staffing-agency.com", "Hello", "I am reaching out about a role at Globex")
    assert r.application is a


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


def raw_html(mid, sender, subject, body, ts):
    import base64
    data = base64.urlsafe_b64encode(body.encode()).decode()
    return {"id": mid, "threadId": "t" + mid, "internalDate": str(ts * 1000), "payload": {
        "mimeType": "multipart/alternative", "headers": [{"name": "From", "value": sender}, {"name": "Subject", "value": subject}],
        "parts": [{"mimeType": "text/html", "body": {"data": data}}]}}


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
    assert app.status == "interview_call"
    steps = [(h.previous_status, h.new_status, h.change_source) for h in db.scalars(select(ApplicationHistory).where(ApplicationHistory.application_id == app.id))]
    assert ("sent", "viewed", "gmail") in steps and ("viewed", "interview_call", "gmail") in steps
    db.refresh(conn)
    assert conn.history_id == "999" and conn.sync_status == "idle" and conn.last_synced_at is not None


def test_sync_is_idempotent_and_never_downgrades(db, user):
    app = add_app(db, user, "Backend Developer", "ABC", status="accepted")
    connect(db, user)
    msgs = {"m1": raw("m1", "ABC <hr@abc.com>", "Interview Invitation — Backend Developer", "Please schedule an interview.", 1_800_000_100)}
    run(db, user, FakeClient(msgs))
    run(db, user, FakeClient(msgs))
    assert db.query(Email).count() == 1
    db.refresh(app)
    assert app.status == "accepted"  # an accepted application is never downgraded by an email


def test_sync_refreshes_an_existing_application_from_linked_gmail_evidence(db, user):
    app = add_app(db, user, "Backend Developer", "ABC")
    connect(db, user)
    email = Email(
        user_id=user.id, gmail_message_id="existing", gmail_thread_id="t-existing",
        sender="ABC Recruiting <jobs@abc.com>", subject="Your application was viewed",
        email_body_excerpt="The hiring team viewed your application.", received_at=datetime.now(timezone.utc),
        classification="under_review", classification_confidence=0.9,
        processing_status="matched",
    )
    db.add(email)
    db.flush()
    db.add(ApplicationEmail(application_id=app.id, email_id=email.id, match_confidence=0.95))
    db.commit()

    result = run(db, user, FakeClient({}))

    db.refresh(app)
    assert result.status_updates == 1
    assert app.status == "viewed"
    history = list(db.scalars(select(ApplicationHistory).where(ApplicationHistory.application_id == app.id)))
    assert history[-1].change_source == "gmail"


def test_ambiguous_email_is_matched_automatically(db, user):
    a = add_app(db, user, "Backend Developer", "ABC")
    b = add_app(db, user, "Data Engineer", "ABC")
    connect(db, user)
    run(db, user, FakeClient({"m1": raw("m1", "ABC <hr@abc.com>", "Update on your application", "Unfortunately we will not be moving forward.", 1_800_000_100)}))
    email = db.scalar(select(Email))
    assert email.processing_status == "matched"
    assert email.links[0].application_id == b.id
    db.refresh(a), db.refresh(b)
    assert a.status == b.status == "sent"


def test_sync_retries_unmatched_email_after_an_application_is_added(db, user):
    connect(db, user)
    message = raw(
        "m1", "Globex Careers <jobs@globex.com>", "Your application is under review",
        "We are reviewing your application for Backend Developer.", 1_800_000_100,
    )
    run(db, user, FakeClient({"m1": message}))
    email = db.scalar(select(Email))
    assert email.processing_status == "needs_review"

    app = add_app(db, user, "Backend Developer", "Globex")
    run(db, user, FakeClient({}))

    db.refresh(email), db.refresh(app)
    assert email.processing_status == "matched"
    assert email.links[0].application_id == app.id
    assert app.status == "viewed"


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
    assert db.scalar(select(JobApplication).where(JobApplication.user_id == other.id)).status == "sent"


def test_linkedin_alert_syncs_listings_without_creating_email_activity(db, user):
    connect(db, user)
    html = '''<html><body><a href="https://www.linkedin.com/jobs/view/12345?tracking=alert">Backend Engineer at Acme</a><p>Build reliable services for a growing product team.</p>
    <a href="https://www.linkedin.com/jobs/view/67890">Data Engineer</a></body></html>'''
    result = run(db, user, FakeClient({"m1": raw_html("m1", "LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>", "Job alert: new jobs for you", html, 1_800_000_100)}))
    alerts = db.scalars(select(JobAlert).order_by(JobAlert.position)).all()
    assert result.job_alerts == 2
    assert [(a.job_title, a.company_name) for a in alerts] == [("Backend Engineer", "Acme"), ("Data Engineer", None)]
    assert alerts[0].description == "Build reliable services for a growing product team."
    assert alerts[0].job_url.startswith("https://www.linkedin.com/jobs/view/12345")
    assert db.query(Email).count() == 0


def test_linkedin_alerts_older_than_a_week_are_not_imported(db, user):
    connect(db, user)
    html = '<a href="https://www.linkedin.com/jobs/view/12345">Backend Engineer at Acme</a>'
    old_timestamp = int((datetime.now(timezone.utc) - timedelta(days=8)).timestamp())
    result = run(db, user, FakeClient({"m1": raw_html("m1", "LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>", "Job alert: new jobs for you", html, old_timestamp)}))
    assert result.job_alerts == 0
    assert db.query(JobAlert).count() == 0


def test_job_alert_list_excludes_entries_older_than_a_week(db, user):
    now = datetime.now(timezone.utc)
    recent = JobAlert(user_id=user.id, gmail_message_id="recent", position=0, job_title="Recent role", job_url="https://www.linkedin.com/jobs/view/1", received_at=now)
    old = JobAlert(user_id=user.id, gmail_message_id="old", position=0, job_title="Old role", job_url="https://www.linkedin.com/jobs/view/2", received_at=now - timedelta(days=8))
    db.add_all([recent, old])
    db.commit()

    alerts, total = job_alert_service.list_alerts(db, user.id, page=1, page_size=20)
    assert total == 1
    assert [alert.job_title for alert in alerts] == ["Recent role"]


def test_confirmation_email_creates_and_updates_an_application_for_overview(db, user):
    connect(db, user)
    messages = {
        "m1": raw("m1", "Acme Careers <jobs@acme.com>", "Your application for Backend Engineer at Acme",
                  "Thank you for applying. We received your application.", 1_800_000_100),
        "m2": raw("m2", "Acme Careers <jobs@acme.com>", "Interview invitation — Backend Engineer",
                  "We would like to invite you to interview for Backend Engineer at Acme.", 1_800_000_200),
    }
    result = run(db, user, FakeClient(messages))
    app = db.scalar(select(JobApplication).where(JobApplication.user_id == user.id))
    emails = db.scalars(select(Email).where(Email.user_id == user.id)).all()
    assert result.applications_created == 1
    assert (app.job_title, app.company_name, app.status, app.platform.name) == ("Backend Engineer", "Acme", "interview_call", "Direct Email")
    assert all(email.processing_status == "matched" for email in emails)


def test_existing_linkedin_confirmation_is_enriched_and_backfilled(db, user):
    connect(db, user)
    email = Email(
        user_id=user.id, gmail_message_id="existing", sender="LinkedIn <jobs-noreply@linkedin.com>",
        subject="Your application was sent to Hire Feed",
        email_body_excerpt="Your application was sent to Hire Feed Software Engineer (Remote) Hire Feed Pakistan View job",
        received_at=datetime.now(timezone.utc), classification="application_confirmation", processing_status="needs_review",
        extracted_company="Hire Feed",
    )
    db.add(email)
    db.commit()
    result = run(db, user, FakeClient({}))
    app = db.scalar(select(JobApplication).where(JobApplication.user_id == user.id))
    assert result.confirmations_enriched == result.applications_created == 1
    assert (app.job_title, app.company_name, app.status) == ("Software Engineer (Remote)", "Hire Feed", "sent")
