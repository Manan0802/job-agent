import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api.routes import outreach as outreach_route
from backend.db.database import init_db
from backend.main import app
from backend.schemas.outreach import OutreachDraft
from backend.schemas.profile import Personal, Profile
from backend.services.contact_store import save_contacts

client = TestClient(app)

PROFILE = Profile(personal=Personal(name="Manan"))

CONTACT = {
    "id": "c1", "name": "Asha Rao", "target_company": "Zepto",
    "current_role": "SDE-2", "linkedin_url": "https://linkedin.com/in/asha-rao",
    "email": "asha@example.com", "degree_type": "1st", "warmth_score": 5,
    "warmth_reasons": '["DTU alumni"]',
}

DRAFT = OutreachDraft(
    message="Hey Asha! Would you be open to referring me?",
    tone="casual", message_type="alumni_dm", channel="linkedin_dm",
)


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "o.db"))
    init_db()
    save_contacts([CONTACT])


def _draft_for(contact_id="c1", **body):
    with patch.object(outreach_route, "load_profile", return_value=PROFILE), \
         patch.object(outreach_route, "draft_message", return_value=DRAFT):
        return client.post("/api/v1/outreach/draft",
                           json={"contact_id": contact_id, **body})


def test_drafting_returns_the_message_and_how_to_send_it(db):
    resp = _draft_for()

    assert resp.status_code == 200
    body = resp.json()
    assert body["body"].startswith("Hey Asha")
    assert body["status"] == "draft"
    assert body["send"]["copy_text"] == DRAFT.message
    assert body["send"]["instructions"]


def test_drafting_for_an_unknown_contact_is_refused(db):
    assert _draft_for(contact_id="nope").status_code == 404


def test_drafting_without_a_profile_says_to_upload_a_resume(db):
    with patch.object(outreach_route, "load_profile", return_value=None):
        resp = client.post("/api/v1/outreach/draft", json={"contact_id": "c1"})

    assert resp.status_code == 400
    assert "resume" in resp.json()["detail"].lower()


def test_the_drafter_is_given_the_contact_it_was_asked_about(db):
    with patch.object(outreach_route, "load_profile", return_value=PROFILE), \
         patch.object(outreach_route, "draft_message", return_value=DRAFT) as draft:
        client.post("/api/v1/outreach/draft",
                    json={"contact_id": "c1", "message_type": "cold_intro"})

    assert draft.call_args[0][0]["name"] == "Asha Rao"
    assert draft.call_args.kwargs["message_type"] == "cold_intro"


def test_the_drafter_is_told_which_job_the_message_is_about(db):
    """A live draft said 'if there's a relevant SDE-1 opening' when the role was
    SDE-2 Backend: job_id was accepted by the API and then never used."""
    from backend.services.job_store import save_jobs

    save_jobs([{"id": "j1", "title": "SDE-2 Backend", "company": "Zepto",
                "description": "Build backend systems", "url": "https://x.com/j1"}])

    with patch.object(outreach_route, "load_profile", return_value=PROFILE), \
         patch.object(outreach_route, "draft_message", return_value=DRAFT) as draft:
        client.post("/api/v1/outreach/draft", json={"contact_id": "c1", "job_id": "j1"})

    assert draft.call_args.kwargs["job"]["title"] == "SDE-2 Backend"


def test_drafting_still_works_when_no_job_is_named(db):
    with patch.object(outreach_route, "load_profile", return_value=PROFILE), \
         patch.object(outreach_route, "draft_message", return_value=DRAFT) as draft:
        client.post("/api/v1/outreach/draft", json={"contact_id": "c1"})

    assert draft.call_args.kwargs["job"] is None


def test_the_user_can_rewrite_the_draft(db):
    message_id = _draft_for().json()["id"]

    resp = client.put(f"/api/v1/outreach/{message_id}",
                      json={"body": "My own words entirely."})

    assert resp.status_code == 200
    assert resp.json()["body"] == "My own words entirely."


def test_approving_does_not_send(db):
    message_id = _draft_for().json()["id"]

    body = client.post(f"/api/v1/outreach/{message_id}/approve").json()

    assert body["status"] == "approved"
    assert body["sent_at"] is None
    assert body["send"]["url"]           # the user still has to go and send it


def test_marking_sent_records_it_against_the_contact_too(db):
    """The tracker needs to know this person has been contacted."""
    from backend.services.contact_store import load_contacts

    message_id = _draft_for().json()["id"]
    client.post(f"/api/v1/outreach/{message_id}/approve")
    body = client.post(f"/api/v1/outreach/{message_id}/sent").json()

    assert body["status"] == "sent" and body["sent_at"]
    assert load_contacts("Zepto")[0]["outreach_status"] == "sent"


def test_skipping_a_contact_is_remembered(db):
    message_id = _draft_for().json()["id"]

    assert client.post(f"/api/v1/outreach/{message_id}/skip").json()["status"] == "skipped"


def test_acting_on_a_message_that_does_not_exist_is_refused(db):
    assert client.post("/api/v1/outreach/nope/approve").status_code == 404


def test_listing_shows_what_is_waiting_for_review(db):
    _draft_for()

    body = client.get("/api/v1/outreach").json()

    assert body["count"] == 1
    assert body["messages"][0]["contact_name"] == "Asha Rao"


def test_listing_can_be_narrowed_to_what_still_needs_approval(db):
    message_id = _draft_for().json()["id"]
    client.post(f"/api/v1/outreach/{message_id}/approve")

    assert client.get("/api/v1/outreach?status=draft").json()["count"] == 0
    assert client.get("/api/v1/outreach?status=approved").json()["count"] == 1


def test_listing_is_empty_before_anything_is_drafted(db):
    body = client.get("/api/v1/outreach").json()
    assert body["count"] == 0 and body["messages"] == []
