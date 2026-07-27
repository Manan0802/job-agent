"""The application pipeline: where every job stands, and what is owed next.

Losing track of an application is the failure this module exists to prevent,
so a stage change always sets the next follow-up date.
"""

import pytest

from backend.db.database import init_db
from backend.services.application_store import (
    PIPELINE_STAGES,
    add_note,
    load_applications,
    move_stage,
    track_job,
)


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    init_db()


JOB = {"id": "j1", "title": "SDE-2 Backend", "company": "Zepto",
       "url": "https://zepto.com/jobs/1", "source_engine": "jobspy:linkedin"}


def test_tracking_a_job_starts_it_as_saved(db):
    app_id = track_job(JOB)

    app = load_applications()[0]
    assert app["id"] == app_id
    assert app["status"] == "saved"
    assert app["company_name"] == "Zepto"
    assert app["role_title"] == "SDE-2 Backend"
    assert app["source"] == "jobspy:linkedin"


def test_tracking_the_same_job_twice_does_not_duplicate_it(db):
    track_job(JOB)
    track_job(JOB)
    assert len(load_applications()) == 1


def test_tracking_again_never_rewinds_progress(db):
    """Re-saving a job you already interviewed for must not reset it."""
    app_id = track_job(JOB)
    move_stage(app_id, "interview_scheduled")
    track_job(JOB)

    assert load_applications()[0]["status"] == "interview_scheduled"


def test_moving_through_the_pipeline(db):
    app_id = track_job(JOB)

    for stage in ("applied", "interview_scheduled", "offer_received"):
        move_stage(app_id, stage)
        assert load_applications()[0]["status"] == stage


def test_applying_records_when(db):
    app_id = track_job(JOB)
    move_stage(app_id, "applied")

    assert load_applications()[0]["applied_date"]


def test_an_interview_and_an_offer_record_their_own_dates(db):
    app_id = track_job(JOB)
    move_stage(app_id, "interview_scheduled")
    assert load_applications()[0]["interview_date"]

    move_stage(app_id, "offer_received")
    assert load_applications()[0]["offer_date"]


def test_an_open_application_always_owes_a_next_check(db):
    """This is the whole point: nothing should quietly go stale."""
    app_id = track_job(JOB)
    move_stage(app_id, "applied")

    assert load_applications()[0]["follow_up_due"]


def test_a_finished_application_stops_asking_for_follow_up(db):
    app_id = track_job(JOB)
    move_stage(app_id, "applied")
    move_stage(app_id, "rejected")

    assert load_applications()[0]["follow_up_due"] is None


def test_an_unknown_stage_is_refused(db):
    app_id = track_job(JOB)
    with pytest.raises(ValueError, match="stage"):
        move_stage(app_id, "hired_probably")


def test_moving_an_application_that_does_not_exist_is_refused(db):
    with pytest.raises(KeyError):
        move_stage("nope", "applied")


def test_a_referral_application_remembers_who_referred(db):
    app_id = track_job(JOB, applied_via="referral", referral_contact_id="c1")

    app = load_applications()[0]
    assert app["applied_via"] == "referral"
    assert app["referral_contact_id"] == "c1"


def test_notes_accumulate_rather_than_overwrite(db):
    app_id = track_job(JOB)
    add_note(app_id, "Recruiter called")
    add_note(app_id, "Asked about system design")

    notes = load_applications()[0]["notes"]
    assert "Recruiter called" in notes and "Asked about system design" in notes


def test_the_pipeline_can_be_filtered_by_stage(db):
    first = track_job(JOB)
    track_job({**JOB, "id": "j2", "title": "SDE-1", "company": "Swiggy"})
    move_stage(first, "applied")

    assert [a["company_name"] for a in load_applications(status="applied")] == ["Zepto"]
    assert len(load_applications()) == 2


def test_the_stages_run_from_saved_to_a_final_answer(db):
    assert PIPELINE_STAGES[0] == "saved"
    assert {"accepted", "rejected"} <= set(PIPELINE_STAGES)
