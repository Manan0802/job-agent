"""Alerting only on jobs the user has not been told about.

A hunt that runs on a schedule re-finds the same listings every time. Alerting
on all of them daily trains the user to ignore the alerts.
"""

import pytest

from backend.db.database import init_db
from backend.services.job_store import load_jobs, save_jobs
from backend.services.new_matches import claim_new_matches


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "n.db"))
    init_db()


def _job(job_id, score):
    return {"id": job_id, "title": f"Role {job_id}", "company": "Zepto",
            "url": f"https://x.com/{job_id}", "llm_score": score}


def test_strong_matches_come_back_the_first_time(db):
    save_jobs([_job("j1", 88.0), _job("j2", 72.0)])

    fresh = claim_new_matches(min_score=70)

    assert {j["id"] for j in fresh} == {"j1", "j2"}


def test_the_same_job_is_not_reported_twice(db):
    save_jobs([_job("j1", 88.0)])
    claim_new_matches(min_score=70)

    assert claim_new_matches(min_score=70) == []


def test_a_job_found_later_is_still_reported(db):
    save_jobs([_job("j1", 88.0)])
    claim_new_matches(min_score=70)

    save_jobs([_job("j2", 91.0)])
    assert [j["id"] for j in claim_new_matches(min_score=70)] == ["j2"]


def test_weak_matches_are_not_worth_an_alert(db):
    save_jobs([_job("j1", 88.0), _job("j2", 40.0)])

    assert [j["id"] for j in claim_new_matches(min_score=70)] == ["j1"]


def test_a_weak_job_can_still_be_reported_if_it_is_rescored_higher(db):
    """Claiming must not silently burn a job that was not worth alerting on."""
    save_jobs([_job("j1", 40.0)])
    claim_new_matches(min_score=70)

    save_jobs([_job("j1", 85.0)])
    assert [j["id"] for j in claim_new_matches(min_score=70)] == ["j1"]


def test_unscored_jobs_are_never_alerted(db):
    save_jobs([{"id": "j1", "title": "Role", "company": "Zepto", "llm_score": None}])
    assert claim_new_matches(min_score=70) == []


def test_matches_come_back_best_first(db):
    save_jobs([_job("j1", 72.0), _job("j2", 95.0), _job("j3", 80.0)])

    assert [j["id"] for j in claim_new_matches(min_score=70)] == ["j2", "j3", "j1"]


def test_claiming_marks_them_so_a_crash_mid_alert_does_not_repeat_forever(db):
    save_jobs([_job("j1", 88.0)])
    claim_new_matches(min_score=70)

    assert load_jobs()[0]["alerted_at"]


def test_nothing_to_report_is_not_an_error(db):
    assert claim_new_matches(min_score=70) == []
