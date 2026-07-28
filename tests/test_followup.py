"""Following up on a message that got no reply.

The tracker already tells the user "no reply yet — send a follow-up?" but
there was no way to act on it. A good follow-up also has to know what was
already said, or it just repeats the pitch.
"""

import json

import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.agents import outreach_drafter
from backend.api.routes import outreach as outreach_route
from backend.db.database import init_db
from backend.main import app
from backend.schemas.outreach import OutreachDraft
from backend.schemas.profile import Personal, Profile
from backend.services.contact_store import save_contacts
from backend.services.message_store import approve_message, load_messages, mark_sent, save_message

client = TestClient(app)

PROFILE = Profile(personal=Personal(name="Manan"))
CONTACT = {"id": "c1", "name": "Asha Rao", "target_company": "Zepto",
           "linkedin_url": "https://linkedin.com/in/asha-rao", "warmth_reasons": '["DTU alumni"]'}

ORIGINAL = "Hey Asha! Fellow DTU here. Would you be open to referring me?"
NUDGE = OutreachDraft(message="Hey Asha, just bumping this in case it got buried.",
                      message_type="followup", channel="linkedin_dm")


@pytest.fixture
def sent(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "fu.db"))
    init_db()
    save_contacts([CONTACT])
    message_id = save_message({"contact_id": "c1", "message_type": "alumni_dm",
                               "channel": "linkedin_dm", "body": ORIGINAL})
    approve_message(message_id)
    mark_sent(message_id)
    return message_id


def test_a_follow_up_can_be_drafted_from_a_sent_message(sent):
    with patch.object(outreach_route, "load_profile", return_value=PROFILE), \
         patch.object(outreach_route, "draft_message", return_value=NUDGE):
        resp = client.post(f"/api/v1/outreach/{sent}/follow-up")

    assert resp.status_code == 200
    body = resp.json()
    assert body["message_type"] == "followup"
    assert body["status"] == "draft"
    assert body["contact_name"] == "Asha Rao"


def test_the_follow_up_knows_what_was_already_said(sent):
    """Without the original, the model just writes the same pitch again."""
    with patch.object(outreach_route, "load_profile", return_value=PROFILE), \
         patch.object(outreach_route, "draft_message", return_value=NUDGE) as draft:
        client.post(f"/api/v1/outreach/{sent}/follow-up")

    assert draft.call_args.kwargs["previous_message"] == ORIGINAL
    assert draft.call_args.kwargs["message_type"] == "followup"


def test_the_original_message_is_kept(sent):
    """A follow-up is a new message, not a rewrite of what you sent."""
    with patch.object(outreach_route, "load_profile", return_value=PROFILE), \
         patch.object(outreach_route, "draft_message", return_value=NUDGE):
        client.post(f"/api/v1/outreach/{sent}/follow-up")

    messages = load_messages(contact_id="c1")
    assert len(messages) == 2
    assert any(m["body"] == ORIGINAL and m["status"] == "sent" for m in messages)


def test_following_up_on_something_you_never_sent_is_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "d.db"))
    init_db()
    save_contacts([CONTACT])
    message_id = save_message({"contact_id": "c1", "body": "still a draft"})

    with patch.object(outreach_route, "load_profile", return_value=PROFILE):
        resp = client.post(f"/api/v1/outreach/{message_id}/follow-up")

    assert resp.status_code == 400
    assert "sent" in resp.json()["detail"].lower()


def test_following_up_on_a_message_that_does_not_exist_is_refused(sent):
    assert client.post("/api/v1/outreach/nope/follow-up").status_code == 404


# --- what the drafter does with the previous message ---

GOOD = json.dumps({"message": "Hey Asha, bumping this once.", "tone": "casual",
                   "personalization_elements": []})


def test_the_drafter_shows_the_model_the_earlier_message():
    with patch.object(outreach_drafter, "complete", return_value=GOOD) as c:
        outreach_drafter.draft_message(
            {"name": "Asha", "current_company": "Zepto"}, PROFILE,
            message_type="followup", previous_message=ORIGINAL)

    prompt = c.call_args[0][0]
    assert ORIGINAL in prompt
    assert "already sent" in prompt.lower() or "previous" in prompt.lower()


def test_a_follow_up_is_told_not_to_reintroduce_the_sender():
    """A real follow-up came back opening 'I'm Manan Kumar, an SDE-1 at...' —
    the prompt's general rule to introduce the sender was fighting the
    follow-up's whole purpose."""
    with patch.object(outreach_drafter, "complete", return_value=GOOD) as c:
        outreach_drafter.draft_message(
            {"name": "Asha", "current_company": "Zepto"}, PROFILE,
            message_type="followup", previous_message=ORIGINAL)

    prompt = c.call_args[0][0].lower()
    assert "introduce" in prompt          # explicitly overridden
    assert "know who you are" in prompt or "already know" in prompt


def test_a_first_message_still_introduces_the_sender():
    with patch.object(outreach_drafter, "complete", return_value=GOOD) as c:
        outreach_drafter.draft_message({"name": "Asha", "current_company": "Zepto"}, PROFILE)

    assert "do not introduce" not in c.call_args[0][0].lower()


def test_a_first_message_carries_no_previous_message():
    with patch.object(outreach_drafter, "complete", return_value=GOOD) as c:
        outreach_drafter.draft_message({"name": "Asha", "current_company": "Zepto"}, PROFILE)

    assert "already sent" not in c.call_args[0][0].lower()
