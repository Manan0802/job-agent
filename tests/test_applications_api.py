import pytest

from fastapi.testclient import TestClient

from backend.db.database import init_db
from backend.main import app
from backend.services.job_store import save_jobs

client = TestClient(app)

JOB = {"id": "j1", "title": "SDE-2 Backend", "company": "Zepto",
       "url": "https://zepto.com/jobs/1", "source_engine": "yc", "llm_score": 88.0}


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "a.db"))
    init_db()
    save_jobs([JOB])


def _track(job_id="j1", **body):
    return client.post("/api/v1/applications/track", json={"job_id": job_id, **body})


def test_tracking_a_job_puts_it_in_the_pipeline(db):
    resp = _track()

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "saved"
    assert body["company_name"] == "Zepto"
    assert body["role_title"] == "SDE-2 Backend"


def test_tracking_a_job_that_does_not_exist_is_refused(db):
    assert _track(job_id="nope").status_code == 404


def test_tracking_records_that_it_came_through_a_referral(db):
    body = _track(applied_via="referral", referral_contact_id="c1").json()

    assert body["applied_via"] == "referral"
    assert body["referral_contact_id"] == "c1"


def test_moving_a_stage(db):
    app_id = _track().json()["id"]

    body = client.post(f"/api/v1/applications/{app_id}/stage",
                       json={"status": "applied"}).json()

    assert body["status"] == "applied"
    assert body["applied_date"]


def test_an_invented_stage_is_rejected_with_the_real_options(db):
    app_id = _track().json()["id"]

    resp = client.post(f"/api/v1/applications/{app_id}/stage",
                       json={"status": "hired_probably"})

    assert resp.status_code == 400
    assert "interview_scheduled" in resp.json()["detail"]


def test_acting_on_an_application_that_does_not_exist_is_refused(db):
    assert client.post("/api/v1/applications/nope/stage",
                       json={"status": "applied"}).status_code == 404


def test_notes_can_be_added_as_things_happen(db):
    app_id = _track().json()["id"]

    body = client.post(f"/api/v1/applications/{app_id}/note",
                       json={"note": "Recruiter called"}).json()

    assert "Recruiter called" in body["notes"]


def test_an_offer_amount_can_be_recorded(db):
    app_id = _track().json()["id"]
    client.post(f"/api/v1/applications/{app_id}/stage", json={"status": "offer_received"})

    body = client.post(f"/api/v1/applications/{app_id}/offer",
                       json={"amount": 2400000, "currency": "INR"}).json()

    assert body["offer_amount"] == 2400000
    assert body["offer_currency"] == "INR"


def test_listing_shows_the_whole_pipeline(db):
    _track()
    body = client.get("/api/v1/applications").json()

    assert body["count"] == 1
    assert body["applications"][0]["company_name"] == "Zepto"


def test_listing_can_be_narrowed_to_one_stage(db):
    app_id = _track().json()["id"]
    client.post(f"/api/v1/applications/{app_id}/stage", json={"status": "applied"})

    assert client.get("/api/v1/applications?status=applied").json()["count"] == 1
    assert client.get("/api/v1/applications?status=saved").json()["count"] == 0


def test_reminders_are_reachable_and_not_mistaken_for_an_application_id(db):
    """`/reminders` must route to the reminders view, not to an application."""
    resp = client.get("/api/v1/applications/reminders")

    assert resp.status_code == 200
    assert "reminders" in resp.json()


def test_stats_report_the_pipeline(db):
    app_id = _track().json()["id"]
    client.post(f"/api/v1/applications/{app_id}/stage", json={"status": "applied"})

    stats = client.get("/api/v1/applications/stats").json()

    assert stats["total"] == 1
    assert stats["applied"] == 1
    assert stats["by_stage"]["applied"] == 1


def test_stats_work_on_an_empty_tracker(db):
    stats = client.get("/api/v1/applications/stats").json()
    assert stats["total"] == 0 and stats["response_rate"] == 0.0
