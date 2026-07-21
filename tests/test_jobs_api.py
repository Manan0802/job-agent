from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api.routes import jobs as jobs_route
from backend.db.database import init_db
from backend.main import app
from backend.schemas.profile import Profile, Personal
from backend.services.job_store import save_jobs
from backend.utils.dedup import job_id

client = TestClient(app)

PROFILE = Profile(personal=Personal(name="Manan"))


def _stored(company, title, score):
    return {
        "id": job_id(company, title), "title": title, "company": company,
        "location": "Remote", "url": f"https://x.com/{title}", "description": "work",
        "source_engine": "yc", "fetched_at": "2026-07-21", "llm_score": score,
        "llm_breakdown": '{"score": %s}' % score,
    }


def test_hunt_reports_what_the_run_produced(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "h.db"))
    init_db()
    hunt_result = {
        "total_found": 484,
        "scored": [_stored("Zepto", "AI Engineer", 88.0)],
        "alert_sent": True,
    }
    with patch.object(jobs_route, "load_profile", return_value=PROFILE), \
         patch.object(jobs_route, "run_hunt", return_value=hunt_result) as run:
        resp = client.post("/api/v1/jobs/hunt", json={"search_term": "AI engineer"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_found"] == 484
    assert body["scored_count"] == 1
    assert body["alert_sent"] is True
    assert body["jobs"][0]["company"] == "Zepto"
    assert run.call_args.kwargs["search_term"] == "AI engineer"


def test_hunt_without_a_profile_says_to_upload_a_resume(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "np.db"))
    init_db()
    with patch.object(jobs_route, "load_profile", return_value=None):
        resp = client.post("/api/v1/jobs/hunt", json={"search_term": "AI engineer"})

    assert resp.status_code == 400
    assert "resume" in resp.json()["detail"].lower()


def test_hunt_passes_through_search_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "s.db"))
    init_db()
    with patch.object(jobs_route, "load_profile", return_value=PROFILE), \
         patch.object(jobs_route, "run_hunt", return_value={"total_found": 0, "scored": [], "alert_sent": False}) as run:
        client.post("/api/v1/jobs/hunt", json={
            "search_term": "backend engineer", "location": "Bangalore", "top_n": 5,
        })

    assert run.call_args.kwargs["location"] == "Bangalore"
    assert run.call_args.kwargs["top_n"] == 5


def test_listing_returns_saved_jobs_best_first(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "l.db"))
    init_db()
    save_jobs([_stored("Swiggy", "SDE-2", 40.0), _stored("Zepto", "SDE-1", 95.0)])

    body = client.get("/api/v1/jobs").json()
    assert body["count"] == 2
    assert body["jobs"][0]["company"] == "Zepto"


def test_listing_can_be_limited(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "lim.db"))
    init_db()
    save_jobs([_stored(f"Co{i}", f"Role{i}", float(i)) for i in range(5)])

    assert client.get("/api/v1/jobs?limit=2").json()["count"] == 2


def test_listing_omits_the_embedding_blob(tmp_path, monkeypatch):
    """Raw vectors are useless over the wire and bloat the response."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "e.db"))
    init_db()
    save_jobs([dict(_stored("Zepto", "SDE-1", 90.0), embedding=b"\x00\x01\x02")])

    assert "embedding" not in client.get("/api/v1/jobs").json()["jobs"][0]


def test_listing_is_empty_before_any_hunt(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "none.db"))
    init_db()
    body = client.get("/api/v1/jobs").json()
    assert body["count"] == 0 and body["jobs"] == []
