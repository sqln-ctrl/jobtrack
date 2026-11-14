from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import make_client, make_user


def payload(platform_id, **over):
    base = {"job_title": "Python Developer", "company_name": "Startup XYZ", "platform_id": platform_id,
            "application_date": date.today().isoformat(), "status": "sent", "job_url": "", "notes": ""}
    return {**base, **over}


def platform_id(client, name="LinkedIn"):
    return next(p["id"] for p in client.get("/api/v1/platforms").json() if p["name"] == name)


def test_requires_auth_and_csrf(db, user):
    app.dependency_overrides.clear()
    anon = TestClient(app)
    assert anon.get("/api/v1/applications").status_code == 401
    c = make_client(db, user)
    c.headers.pop("X-CSRF-Token")
    assert c.post("/api/v1/applications", json={}).status_code == 403
    app.dependency_overrides.clear()


def test_crud_filters_and_history(client):
    pid = platform_id(client)
    created = client.post("/api/v1/applications", json=payload(pid))
    assert created.status_code == 201 and created.json()["job_url"] is None  # blank strings become null
    app_id = created.json()["id"]
    client.post("/api/v1/applications", json=payload(platform_id(client, "Indeed"), job_title="Full Stack Developer", company_name="ABC"))

    assert client.get("/api/v1/applications", params={"q": "abc"}).json()["total"] == 1
    assert client.get("/api/v1/applications", params={"platform_id": pid}).json()["total"] == 1
    assert client.get("/api/v1/applications", params={"status": "accepted"}).json()["total"] == 0

    r = client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "interview_call", "note": "Recruiter called"})
    assert r.json()["status"] == "interview_call"
    detail = client.get(f"/api/v1/applications/{app_id}").json()
    titles = [e["title"] for e in detail["timeline"]]
    assert titles == ["Application sent", "Status changed to Interview call"]

    assert client.delete(f"/api/v1/applications/{app_id}").status_code == 204
    assert client.get(f"/api/v1/applications/{app_id}").status_code == 404


def test_new_applications_are_recorded_as_sent(client):
    r = client.post("/api/v1/applications", json=payload(platform_id(client), status="sent")).json()
    timeline = client.get(f"/api/v1/applications/{r['id']}").json()["timeline"]
    assert timeline[0]["title"] == "Application sent"


def test_users_cannot_see_or_touch_each_others_data(db, user):
    a = make_client(db, user)
    pid = platform_id(a)
    app_id = a.post("/api/v1/applications", json=payload(pid)).json()["id"]
    custom = a.post("/api/v1/platforms", json={"name": "Wellfound"}).json()["id"]
    app.dependency_overrides.clear()

    b = make_client(db, make_user(db, 2))
    assert b.get(f"/api/v1/applications/{app_id}").status_code == 404
    assert b.delete(f"/api/v1/applications/{app_id}").status_code == 404
    assert b.patch(f"/api/v1/applications/{app_id}/status", json={"status": "accepted"}).status_code == 404
    assert b.get("/api/v1/applications").json()["total"] == 0
    assert all(p["name"] != "Wellfound" for p in b.get("/api/v1/platforms").json())
    assert b.delete(f"/api/v1/platforms/{custom}").status_code == 404
    assert b.post("/api/v1/applications", json=payload(custom)).status_code == 404  # cannot use someone else's platform
    app.dependency_overrides.clear()


def test_platform_rules(client):
    assert client.post("/api/v1/platforms", json={"name": "linkedin"}).status_code == 409
    custom = client.post("/api/v1/platforms", json={"name": "Wellfound"}).json()["id"]
    client.post("/api/v1/applications", json=payload(custom))
    assert client.delete(f"/api/v1/platforms/{custom}").status_code == 409
    assert client.delete(f"/api/v1/platforms/{platform_id(client)}").status_code == 404  # defaults are read-only


def test_dashboard_and_interviews(client):
    pid = platform_id(client)
    a = client.post("/api/v1/applications", json=payload(pid, status="interview_call")).json()["id"]
    client.post("/api/v1/applications", json=payload(pid, status="accepted"))
    client.post("/api/v1/applications", json=payload(pid, status="rejected"))
    iv = client.post("/api/v1/interviews", json={"application_id": a, "interview_date": "2099-01-01T10:00:00Z", "interview_type": "Technical"})
    assert iv.status_code == 201 and iv.json()["company_name"] == "Startup XYZ"
    stats = client.get("/api/v1/dashboard/stats").json()
    assert (stats["total"], stats["interview_calls"], stats["accepted"], stats["rejected"], stats["upcoming_interviews"]) == (3, 1, 1, 1, 1)
    assert client.get("/api/v1/dashboard/platforms").json()[0] == {"platform_id": pid, "name": "LinkedIn", "count": 3}
    assert len(client.get("/api/v1/interviews", params={"upcoming": True}).json()) == 1


def test_manual_email_match_actions_are_not_exposed(client):
    assert client.post("/api/v1/emails/1/match", json={"application_id": 1}).status_code == 404
    assert client.post("/api/v1/emails/1/ignore").status_code == 404
