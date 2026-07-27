"""Reminders and stats — what the tracker is actually for.

Reminders answer "what have I let go stale?"; stats answer "is any of this
working, and which source is worth my time?".
"""

from datetime import datetime, timedelta, timezone

import pytest

from backend.db.database import init_db
from backend.services.application_store import move_stage, track_job
from backend.services.tracker_insights import due_reminders, pipeline_stats


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    init_db()


def _job(job_id="j1", company="Zepto", source="jobspy:linkedin"):
    return {"id": job_id, "title": "SDE-2", "company": company,
            "url": f"https://x.com/{job_id}", "source_engine": source}


def _make_overdue(application_id, days=10):
    """Pull the follow-up date into the past without waiting for it."""
    from backend.db.database import get_session
    from backend.db.models import ApplicationRow

    past = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with get_session() as session:
        row = session.get(ApplicationRow, application_id)
        row.follow_up_due = past
        session.commit()


def test_nothing_is_owed_right_after_you_start(db):
    track_job(_job())
    assert due_reminders() == []


def test_an_application_left_alone_too_long_comes_back_as_a_reminder(db):
    app_id = track_job(_job())
    move_stage(app_id, "applied")
    _make_overdue(app_id)

    reminders = due_reminders()
    assert len(reminders) == 1
    assert reminders[0]["company_name"] == "Zepto"
    assert reminders[0]["status"] == "applied"


def test_a_reminder_says_what_to_actually_do(db):
    app_id = track_job(_job())
    move_stage(app_id, "applied")
    _make_overdue(app_id)

    reminder = due_reminders()[0]
    assert reminder["action"]
    assert "follow" in reminder["action"].lower() or "reply" in reminder["action"].lower()


def test_the_suggested_action_fits_the_stage(db):
    interview = track_job(_job("j1"))
    move_stage(interview, "interview_done")
    _make_overdue(interview)

    offer = track_job(_job("j2", company="Swiggy"))
    move_stage(offer, "offer_received")
    _make_overdue(offer)

    actions = {r["company_name"]: r["action"].lower() for r in due_reminders()}
    assert "thank" in actions["Zepto"]
    assert "offer" in actions["Swiggy"] or "decide" in actions["Swiggy"]


def test_a_reminder_says_how_long_it_has_been(db):
    app_id = track_job(_job())
    move_stage(app_id, "applied")
    _make_overdue(app_id, days=10)

    assert due_reminders()[0]["days_overdue"] >= 9


def test_a_finished_application_never_nags(db):
    app_id = track_job(_job())
    move_stage(app_id, "applied")
    _make_overdue(app_id)
    move_stage(app_id, "rejected")

    assert due_reminders() == []


def test_the_most_overdue_comes_first(db):
    old = track_job(_job("j1"))
    recent = track_job(_job("j2", company="Swiggy"))
    move_stage(old, "applied")
    move_stage(recent, "applied")
    _make_overdue(old, days=20)
    _make_overdue(recent, days=2)

    assert [r["company_name"] for r in due_reminders()] == ["Zepto", "Swiggy"]


def test_stats_on_an_empty_tracker_are_zeroes_not_errors(db):
    stats = pipeline_stats()
    assert stats["total"] == 0
    assert stats["response_rate"] == 0.0
    assert stats["best_source"] is None


def test_stats_count_the_pipeline_by_stage(db):
    first = track_job(_job("j1"))
    track_job(_job("j2", company="Swiggy"))
    move_stage(first, "applied")

    stats = pipeline_stats()
    assert stats["total"] == 2
    assert stats["by_stage"]["applied"] == 1
    assert stats["by_stage"]["saved"] == 1


def test_response_rate_is_replies_over_applications(db):
    """Two applied, one got as far as an interview."""
    replied = track_job(_job("j1"))
    track_job(_job("j2", company="Swiggy"))
    move_stage(replied, "applied")
    move_stage(replied, "interview_scheduled")
    move_stage(track_job(_job("j2", company="Swiggy")), "applied")

    stats = pipeline_stats()
    assert stats["applied"] == 2
    assert stats["responded"] == 1
    assert stats["response_rate"] == pytest.approx(50.0)


def test_a_job_you_only_saved_does_not_drag_the_response_rate_down(db):
    applied = track_job(_job("j1"))
    track_job(_job("j2", company="Swiggy"))       # saved, never applied
    move_stage(applied, "applied")
    move_stage(applied, "interview_scheduled")

    assert pipeline_stats()["response_rate"] == pytest.approx(100.0)


def test_stats_track_what_is_still_live_and_what_landed(db):
    live = track_job(_job("j1"))
    done = track_job(_job("j2", company="Swiggy"))
    move_stage(live, "interview_scheduled")
    move_stage(done, "rejected")

    stats = pipeline_stats()
    assert stats["active"] == 1
    assert stats["offers"] == 0


def test_stats_name_the_source_that_actually_gets_replies(db):
    """The point of this number is to stop wasting time on dead channels."""
    good = track_job(_job("j1", source="yc"))
    bad = track_job(_job("j2", company="Swiggy", source="jobspy:linkedin"))
    move_stage(good, "applied")
    move_stage(good, "interview_scheduled")
    move_stage(bad, "applied")

    stats = pipeline_stats()
    assert stats["best_source"] == "yc"
    assert stats["by_source"]["yc"]["response_rate"] == pytest.approx(100.0)
    assert stats["by_source"]["jobspy:linkedin"]["response_rate"] == pytest.approx(0.0)


def test_a_source_you_never_applied_through_cannot_be_the_best(db):
    """One saved-but-never-applied job should not win on an empty record."""
    track_job(_job("j1", source="never_applied"))
    applied = track_job(_job("j2", company="Swiggy", source="yc"))
    move_stage(applied, "applied")
    move_stage(applied, "offer_received")

    assert pipeline_stats()["best_source"] == "yc"
