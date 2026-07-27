"""When the model can't produce a usable answer, say so in words.

Live runs hit this for real: the fallback model spent its whole budget
reasoning and returned an empty string, and every LLM-backed endpoint answered
with a bare 500 "Internal Server Error". That tells the user nothing and looks
like the app is broken rather than the model being busy.
"""

import io

import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api.routes import outreach as outreach_route
from backend.api.routes import resume as resume_route
from backend.api.routes import tailor as tailor_route
from backend.db.database import init_db
from backend.llm.errors import ModelUnavailable
from backend.main import app
from backend.schemas.profile import Personal, Profile
from backend.services.contact_store import save_contacts
from backend.services.job_store import save_jobs

client = TestClient(app, raise_server_exceptions=False)

PROFILE = Profile(personal=Personal(name="Manan"))
# What the agents actually raise once they have exhausted their retries.
BUSY = ModelUnavailable("could not analyse this job after 3 attempts: Expecting value")


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "f.db"))
    init_db()
    save_jobs([{"id": "j1", "title": "SDE", "company": "Zepto", "description": "x"}])
    save_contacts([{"id": "c1", "name": "Asha", "target_company": "Zepto"}])


def _assert_useful(response):
    assert response.status_code == 503, response.status_code
    detail = response.json()["detail"]
    assert "Internal Server Error" not in detail
    assert "again" in detail.lower()          # tells them what to do


def test_tailoring_says_the_model_is_busy_rather_than_failing_opaquely(db):
    with patch.object(tailor_route, "load_profile", return_value=PROFILE), \
         patch.object(tailor_route, "analyze_fit", side_effect=BUSY):
        _assert_useful(client.post("/api/v1/tailor/analyze", json={"job_id": "j1"}))


def test_a_cover_letter_that_cannot_be_written_says_so(db):
    with patch.object(tailor_route, "load_profile", return_value=PROFILE), \
         patch.object(tailor_route, "draft_cover_letter", side_effect=BUSY):
        _assert_useful(client.post("/api/v1/tailor/cover-letter", json={"job_id": "j1"}))


def test_a_message_that_cannot_be_drafted_says_so(db):
    with patch.object(outreach_route, "load_profile", return_value=PROFILE), \
         patch.object(outreach_route, "draft_message", side_effect=BUSY):
        _assert_useful(client.post("/api/v1/outreach/draft", json={"contact_id": "c1"}))


def test_a_resume_that_cannot_be_parsed_says_so(db):
    with patch.object(resume_route, "parse_resume_pdf", side_effect=BUSY):
        _assert_useful(
            client.post(
                "/api/v1/resume/upload",
                files={"file": ("cv.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            )
        )


def test_a_genuine_bug_is_not_disguised_as_the_model_being_busy(db):
    """Only the model's own give-up is translated; real crashes still surface."""
    with patch.object(tailor_route, "load_profile", return_value=PROFILE), \
         patch.object(tailor_route, "analyze_fit", side_effect=TypeError("real bug")):
        assert client.post("/api/v1/tailor/analyze", json={"job_id": "j1"}).status_code == 500
