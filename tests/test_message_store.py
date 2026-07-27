"""Outreach messages and their lifecycle.

Nothing here sends anything: a message moves draft → approved → sent only
because the user says so, and "sent" is recorded after they send it
themselves.
"""

import pytest

from backend.db.database import init_db
from backend.services.message_store import (
    approve_message,
    load_messages,
    mark_sent,
    save_message,
    skip_message,
    update_message,
)


def _draft(contact_id="c1", **extra):
    return {
        "contact_id": contact_id, "job_id": "j1", "message_type": "referral_request",
        "channel": "linkedin_dm", "subject": None,
        "body": "Hey Asha, saw we both went to DTU...",
        "tone": "casual", **extra,
    }


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "m.db"))
    init_db()


def test_a_new_message_starts_as_an_unsent_draft(db):
    message_id = save_message(_draft())

    stored = load_messages()[0]
    assert stored["id"] == message_id
    assert stored["status"] == "draft"
    assert stored["sent_at"] is None
    assert stored["body"].startswith("Hey Asha")


def test_drafting_again_for_the_same_contact_replaces_the_old_draft(db):
    """Regenerating should not leave stale drafts lying around."""
    save_message(_draft(body="first attempt"))
    save_message(_draft(body="second attempt"))

    messages = load_messages()
    assert len(messages) == 1
    assert messages[0]["body"] == "second attempt"


def test_editing_a_draft_keeps_the_users_words(db):
    message_id = save_message(_draft())
    update_message(message_id, body="My own version, in my own voice.")

    assert load_messages()[0]["body"] == "My own version, in my own voice."


def test_approving_marks_it_ready_but_does_not_send(db):
    message_id = save_message(_draft())
    approve_message(message_id)

    stored = load_messages()[0]
    assert stored["status"] == "approved"
    assert stored["sent_at"] is None      # sending is the user's own action


def test_sending_is_recorded_only_after_the_user_did_it(db):
    message_id = save_message(_draft())
    approve_message(message_id)
    mark_sent(message_id)

    stored = load_messages()[0]
    assert stored["status"] == "sent"
    assert stored["sent_at"]


def test_a_skipped_contact_is_remembered_so_it_is_not_redrafted(db):
    message_id = save_message(_draft())
    skip_message(message_id)

    assert load_messages()[0]["status"] == "skipped"


def test_editing_an_approved_message_sends_it_back_for_review(db):
    """Changing the words after approval must not leave it marked approved."""
    message_id = save_message(_draft())
    approve_message(message_id)
    update_message(message_id, body="actually, let me rephrase")

    assert load_messages()[0]["status"] == "draft"


def test_a_sent_message_is_never_silently_redrafted(db):
    """Re-running outreach must not overwrite what was already sent."""
    message_id = save_message(_draft(body="the message I sent"))
    approve_message(message_id)
    mark_sent(message_id)

    save_message(_draft(body="a fresh draft"))

    messages = load_messages()
    assert len(messages) == 2
    assert any(m["body"] == "the message I sent" and m["status"] == "sent" for m in messages)


def test_messages_can_be_listed_for_one_contact(db):
    save_message(_draft(contact_id="c1"))
    save_message(_draft(contact_id="c2"))

    assert len(load_messages(contact_id="c1")) == 1
    assert len(load_messages()) == 2


def test_messages_can_be_listed_by_status(db):
    first = save_message(_draft(contact_id="c1"))
    save_message(_draft(contact_id="c2"))
    approve_message(first)

    assert [m["contact_id"] for m in load_messages(status="approved")] == ["c1"]


def test_acting_on_a_message_that_does_not_exist_is_refused(db):
    with pytest.raises(KeyError):
        approve_message("nope")
