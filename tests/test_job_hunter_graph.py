"""The graph wires the whole hunt together, so every external call is mocked
and what is asserted is the flow: what reaches the LLM, what gets saved, and
what still works when a piece of the internet is down.
"""

from unittest.mock import patch

import numpy as np
import pytest

from backend.agents import job_hunter_graph as graph
from backend.db.database import init_db
from backend.schemas.profile import Profile, Personal, Skills

PROFILE = Profile(
    personal=Personal(name="Manan"),
    skills=Skills(languages=["Python"], ai_ml=["LangGraph"]),
)


def _job(title, company="Acme", source="jobspy:linkedin"):
    return {
        "title": title, "company": company, "location": "Remote",
        "url": f"https://x.com/{title}", "description": f"{title} work",
        "date_posted": "2026-07-01", "source_engine": source,
        "fetched_at": "2026-07-21T00:00:00Z",
    }


def _emb(*values) -> bytes:
    return np.asarray(values, dtype=np.float32).tobytes()


@pytest.fixture
def hunt_env(tmp_path, monkeypatch):
    """Runs the graph against a temp DB with every network/LLM call stubbed."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "hunt.db"))
    init_db()

    with patch.object(graph, "fetch_jobs", return_value=[_job("AI Engineer")]), \
         patch.object(graph, "fetch_all_remote", return_value=[_job("ML Engineer", source="remotive")]), \
         patch.object(graph, "fetch_yc_jobs", return_value=[_job("Backend Engineer", source="yc")]), \
         patch.object(graph, "embed_profile", return_value=_emb(1.0, 0.0)), \
         patch.object(graph, "prefilter_jobs", side_effect=lambda jobs, emb, top_n: jobs[:top_n]), \
         patch.object(graph, "score_jobs", side_effect=lambda jobs, profile: [
             {**j, "llm_score": 90.0 - i * 10, "llm_breakdown": '{"score": 90}'}
             for i, j in enumerate(jobs)
         ]), \
         patch.object(graph, "send_telegram_alert", return_value=True) as alert:
        yield alert


def test_hunt_returns_scored_jobs_from_every_source(hunt_env):
    result = graph.run_hunt(PROFILE, search_term="engineer")

    assert result["total_found"] == 3
    sources = {j["source_engine"] for j in result["scored"]}
    assert sources == {"jobspy:linkedin", "remotive", "yc"}
    assert all(j["llm_score"] is not None for j in result["scored"])


def test_scored_jobs_are_persisted(hunt_env):
    from backend.services.job_store import load_jobs

    graph.run_hunt(PROFILE, search_term="engineer")
    saved = load_jobs()
    assert len(saved) == 3
    assert saved[0]["llm_score"] == 90.0     # best first
    assert all(j["id"] for j in saved)


def test_an_alert_goes_out_with_the_run_totals(hunt_env):
    graph.run_hunt(PROFILE, search_term="engineer")
    hunt_env.assert_called_once()
    message = hunt_env.call_args[0][0]
    assert "AI Engineer" in message
    assert "3" in message


def test_only_the_shortlist_reaches_the_llm(tmp_path, monkeypatch):
    """Pre-filtering is what keeps the run inside the free tier."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "cap.db"))
    init_db()
    many = [_job(f"Job {i}") for i in range(50)]

    with patch.object(graph, "fetch_jobs", return_value=many), \
         patch.object(graph, "fetch_all_remote", return_value=[]), \
         patch.object(graph, "fetch_yc_jobs", return_value=[]), \
         patch.object(graph, "embed_profile", return_value=_emb(1.0, 0.0)), \
         patch.object(graph, "prefilter_jobs", side_effect=lambda jobs, emb, top_n: jobs[:top_n]), \
         patch.object(graph, "score_jobs", side_effect=lambda jobs, p: jobs) as score, \
         patch.object(graph, "send_telegram_alert", return_value=True):
        graph.run_hunt(PROFILE, search_term="engineer", top_n=5)

    assert len(score.call_args[0][0]) == 5


def test_one_dead_source_does_not_sink_the_hunt(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "dead.db"))
    init_db()

    with patch.object(graph, "fetch_jobs", side_effect=RuntimeError("linkedin blocked")), \
         patch.object(graph, "fetch_all_remote", return_value=[_job("ML Engineer", source="remotive")]), \
         patch.object(graph, "fetch_yc_jobs", return_value=[_job("Backend Engineer", source="yc")]), \
         patch.object(graph, "embed_profile", return_value=_emb(1.0, 0.0)), \
         patch.object(graph, "prefilter_jobs", side_effect=lambda jobs, emb, top_n: jobs[:top_n]), \
         patch.object(graph, "score_jobs", side_effect=lambda jobs, p: [
             {**j, "llm_score": 80.0, "llm_breakdown": "{}"} for j in jobs]), \
         patch.object(graph, "send_telegram_alert", return_value=True):
        result = graph.run_hunt(PROFILE, search_term="engineer")

    assert result["total_found"] == 2


def test_duplicates_across_sources_are_collapsed(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "dupe.db"))
    init_db()
    same = _job("AI Engineer", company="Zepto")

    with patch.object(graph, "fetch_jobs", return_value=[same]), \
         patch.object(graph, "fetch_all_remote", return_value=[dict(same, source_engine="remotive")]), \
         patch.object(graph, "fetch_yc_jobs", return_value=[]), \
         patch.object(graph, "embed_profile", return_value=_emb(1.0, 0.0)), \
         patch.object(graph, "prefilter_jobs", side_effect=lambda jobs, emb, top_n: jobs[:top_n]), \
         patch.object(graph, "score_jobs", side_effect=lambda jobs, p: [
             {**j, "llm_score": 80.0, "llm_breakdown": "{}"} for j in jobs]), \
         patch.object(graph, "send_telegram_alert", return_value=True):
        result = graph.run_hunt(PROFILE, search_term="engineer")

    assert result["total_found"] == 1


def test_a_hunt_that_finds_nothing_finishes_cleanly(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "empty.db"))
    init_db()

    with patch.object(graph, "fetch_jobs", return_value=[]), \
         patch.object(graph, "fetch_all_remote", return_value=[]), \
         patch.object(graph, "fetch_yc_jobs", return_value=[]), \
         patch.object(graph, "embed_profile", return_value=_emb(1.0, 0.0)), \
         patch.object(graph, "prefilter_jobs", return_value=[]), \
         patch.object(graph, "score_jobs", return_value=[]) as score, \
         patch.object(graph, "send_telegram_alert", return_value=True):
        result = graph.run_hunt(PROFILE, search_term="engineer")

    assert result["total_found"] == 0
    assert result["scored"] == []
    score.assert_not_called()      # nothing to score, so no LLM spend


def test_sources_are_fetched_concurrently(hunt_env):
    """Three sequential network calls would make every hunt needlessly slow."""
    import threading
    active, peak = 0, 0
    lock = threading.Lock()

    def slow(*args, **kwargs):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        import time; time.sleep(0.05)
        with lock:
            active -= 1
        return []

    with patch.object(graph, "fetch_jobs", side_effect=slow), \
         patch.object(graph, "fetch_all_remote", side_effect=slow), \
         patch.object(graph, "fetch_yc_jobs", side_effect=slow):
        graph._ingest({"search_term": "engineer", "location": "India"})

    assert peak > 1
