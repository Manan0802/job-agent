"""Interview prep over HTTP."""

import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.db.database import init_db
from backend.main import app
from backend.schemas.profile import Personal, Profile
from backend.services.job_store import save_jobs

REPLY = json.dumps({
    "role_focus": "Whether you can own a Postgres schema under load.",
    "questions": [{"question": "Walk me through a query you made faster.",
                   "why": "The posting leads on throughput.",
                   "answer_from": "The Postgres index at IndiaMART."}],
    "weak_spots": ["Kubernetes"],
    "ask_them": ["Who owns the schema today?"],
})


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "i.db"))
    init_db()
    save_jobs([{"id": "j1", "title": "Backend Engineer", "company": "Zepto",
                "description": "High-throughput order services on Postgres."}])
    return TestClient(app)


def _with_profile():
    return patch("backend.api.routes.interview.load_profile",
                 return_value=Profile(personal=Personal(name="Manan")))


def test_it_prepares_you_for_a_job_you_found(client):
    with _with_profile(), patch("backend.agents.interview_prep.complete", return_value=REPLY):
        resp = client.post("/api/v1/interview/prep", json={"job_id": "j1"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["questions"][0]["question"] == "Walk me through a query you made faster."
    assert body["job"]["company"] == "Zepto"


def test_it_says_whether_anything_would_have_you_overclaim(client):
    """The UI needs this to warn before the user rehearses it."""
    with _with_profile(), patch("backend.agents.interview_prep.complete", return_value=REPLY):
        body = client.post("/api/v1/interview/prep", json={"job_id": "j1"}).json()

    assert "has_unsupported" in body


def test_preparing_for_a_job_that_was_never_found_is_a_404(client):
    with _with_profile():
        resp = client.post("/api/v1/interview/prep", json={"job_id": "nope"})

    assert resp.status_code == 404


def test_preparing_without_a_resume_says_to_upload_one(client):
    with patch("backend.api.routes.interview.load_profile", return_value=None):
        resp = client.post("/api/v1/interview/prep", json={"job_id": "j1"})

    assert resp.status_code == 400
    assert "resume" in resp.json()["detail"].lower()


def test_a_busy_model_is_a_503_not_a_crash(client):
    with _with_profile(), patch("backend.agents.interview_prep.complete", return_value="nope"):
        resp = client.post("/api/v1/interview/prep", json={"job_id": "j1"})

    assert resp.status_code == 503
