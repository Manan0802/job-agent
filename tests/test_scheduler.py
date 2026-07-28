"""Hunting on a schedule.

Without this the app is a tool you remember to open. The PRD's premise was an
agent that checks every few days and tells you what it found.

It is opt-in: a server that started hunting on its own would spend the user's
free tier without being asked.
"""

import pytest
from unittest.mock import MagicMock, patch

from backend.db.database import init_db
from backend.schemas.profile import Personal, Profile
from backend.services import scheduler
from backend.services.job_store import save_jobs

PROFILE = Profile(personal=Personal(name="Manan"))


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "s.db"))
    init_db()


def _settings(**overrides):
    fake = MagicMock()
    fake.hunt_every_hours = overrides.get("hours", 24)
    fake.hunt_search_term = overrides.get("term", "AI engineer")
    fake.hunt_location = overrides.get("location", "India")
    fake.hunt_top_n = overrides.get("top_n", 10)
    fake.alert_min_score = overrides.get("min_score", 70)
    return fake


def test_a_hunt_runs_and_reports_what_it_found(db, monkeypatch):
    monkeypatch.setattr(scheduler, "_settings", _settings())
    save_jobs([{"id": "j1", "title": "AI Engineer", "company": "Zepto",
                "url": "https://x.com/1", "llm_score": 88.0}])

    with patch.object(scheduler, "load_profile", return_value=PROFILE), \
         patch.object(scheduler, "run_hunt", return_value={"total_found": 40}) as hunt, \
         patch.object(scheduler, "send_telegram_alert", return_value=True) as alert:
        result = scheduler.run_scheduled_hunt()

    hunt.assert_called_once()
    assert result["new_matches"] == 1
    assert result["alerted"] is True
    assert "AI Engineer" in alert.call_args[0][0]


def test_a_hunt_that_turns_up_nothing_new_stays_quiet(db, monkeypatch):
    """Daily "nothing new" messages are how an alert gets muted."""
    monkeypatch.setattr(scheduler, "_settings", _settings())

    with patch.object(scheduler, "load_profile", return_value=PROFILE), \
         patch.object(scheduler, "run_hunt", return_value={"total_found": 40}), \
         patch.object(scheduler, "send_telegram_alert") as alert:
        result = scheduler.run_scheduled_hunt()

    alert.assert_not_called()
    assert result["new_matches"] == 0


def test_only_strong_matches_are_worth_waking_someone_for(db, monkeypatch):
    monkeypatch.setattr(scheduler, "_settings", _settings(min_score=70))
    save_jobs([{"id": "j1", "title": "Weak", "company": "X", "llm_score": 45.0}])

    with patch.object(scheduler, "load_profile", return_value=PROFILE), \
         patch.object(scheduler, "run_hunt", return_value={"total_found": 5}), \
         patch.object(scheduler, "send_telegram_alert") as alert:
        scheduler.run_scheduled_hunt()

    alert.assert_not_called()


def test_hunting_without_a_resume_is_skipped_rather_than_crashing(db, monkeypatch):
    monkeypatch.setattr(scheduler, "_settings", _settings())

    with patch.object(scheduler, "load_profile", return_value=None), \
         patch.object(scheduler, "run_hunt") as hunt:
        result = scheduler.run_scheduled_hunt()

    hunt.assert_not_called()
    assert "resume" in result["skipped"].lower()


def test_a_failing_hunt_does_not_kill_the_schedule(db, monkeypatch):
    """One bad night must not stop it from trying tomorrow."""
    monkeypatch.setattr(scheduler, "_settings", _settings())

    with patch.object(scheduler, "load_profile", return_value=PROFILE), \
         patch.object(scheduler, "run_hunt", side_effect=RuntimeError("sources down")):
        result = scheduler.run_scheduled_hunt()

    assert result["error"]


# --- whether it runs at all ---

def test_scheduling_is_off_until_a_search_term_is_set(monkeypatch):
    """A server that started hunting on its own would spend the free tier
    without being asked."""
    monkeypatch.setattr(scheduler, "_settings", _settings(term=""))
    assert scheduler.is_enabled() is False


def test_scheduling_is_off_when_the_interval_is_zero(monkeypatch):
    monkeypatch.setattr(scheduler, "_settings", _settings(hours=0))
    assert scheduler.is_enabled() is False


def test_scheduling_is_on_once_both_are_set(monkeypatch):
    monkeypatch.setattr(scheduler, "_settings", _settings())
    assert scheduler.is_enabled() is True
