import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api.routes import tailor as tailor_route
from backend.db.database import init_db
from backend.main import app
from backend.schemas.profile import Personal, Profile
from backend.schemas.tailoring import FitAnalysis, Suggestion
from backend.services.job_store import save_jobs

client = TestClient(app)

PROFILE = Profile(personal=Personal(name="Manan"))
JOB = {"id": "j1", "title": "Senior Backend Engineer", "company": "Zepto",
       "description": "Distributed systems. Go and Kubernetes required.",
       "url": "https://x.com/j1"}

ANALYSIS = FitAnalysis(
    verdict="Weak fit on the infra requirements.",
    strengths=["RAG pipelines"],
    buried=["Python is only in the skills list"],
    missing=["Kubernetes"],
    suggestions=[
        Suggestion(section="summary", change="Claim distributed systems", why="posting says so",
                   unsupported=["distributed"]),
        Suggestion(section="skills", change="Move Python up", why="posting mentions Python"),
    ],
)


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    init_db()
    save_jobs([JOB])


def test_analysis_separates_what_you_lack_from_what_you_buried(db):
    with patch.object(tailor_route, "load_profile", return_value=PROFILE), \
         patch.object(tailor_route, "analyze_fit", return_value=ANALYSIS):
        body = client.post("/api/v1/tailor/analyze", json={"job_id": "j1"}).json()

    assert body["missing"] == ["Kubernetes"]
    assert body["buried"] == ["Python is only in the skills list"]
    assert body["job"]["title"] == "Senior Backend Engineer"


def test_suggestions_that_overreach_are_marked_for_the_user(db):
    """The user has to see which edits would have them claim something new."""
    with patch.object(tailor_route, "load_profile", return_value=PROFILE), \
         patch.object(tailor_route, "analyze_fit", return_value=ANALYSIS):
        body = client.post("/api/v1/tailor/analyze", json={"job_id": "j1"}).json()

    assert body["has_unsupported"] is True
    assert body["suggestions"][0]["unsupported"] == ["distributed"]
    assert body["suggestions"][1]["unsupported"] == []


def test_analysing_an_unknown_job_is_refused(db):
    with patch.object(tailor_route, "load_profile", return_value=PROFILE):
        assert client.post("/api/v1/tailor/analyze", json={"job_id": "nope"}).status_code == 404


def test_analysing_without_a_profile_says_to_upload_a_resume(db):
    with patch.object(tailor_route, "load_profile", return_value=None):
        resp = client.post("/api/v1/tailor/analyze", json={"job_id": "j1"})

    assert resp.status_code == 400
    assert "resume" in resp.json()["detail"].lower()


def test_a_cover_letter_can_be_drafted_for_a_job(db):
    from backend.agents.resume_tailor import CoverLetter

    with patch.object(tailor_route, "load_profile", return_value=PROFILE), \
         patch.object(tailor_route, "draft_cover_letter",
                      return_value=CoverLetter(body="Dear team...", opening_hook="the RAG work")):
        body = client.post("/api/v1/tailor/cover-letter", json={"job_id": "j1"}).json()

    assert body["body"].startswith("Dear team")
    assert body["opening_hook"]
