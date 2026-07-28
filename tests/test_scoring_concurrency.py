"""Scoring the shortlist concurrently.

Sequential scoring was the slowest part of a hunt: ~4.3s per job, so a
15-job shortlist spent over a minute waiting on one request at a time. The
cap exists because the free tiers are small — Gemini allows 15 requests a
minute — so this goes wide, not unbounded.
"""

import json
import threading
import time

from unittest.mock import patch

from backend.agents import job_scorer
from backend.schemas.profile import Personal, Profile

PROFILE = Profile(personal=Personal(name="Manan"))
JOBS = [{"title": f"Job {i}", "company": "Zepto", "description": "x"} for i in range(8)]
GOOD = json.dumps({"score": 80, "reasoning": "fits"})


def test_jobs_are_scored_concurrently():
    active = peak = 0
    lock = threading.Lock()

    def slow(*args, **kwargs):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.05)
        with lock:
            active -= 1
        return GOOD

    with patch.object(job_scorer, "complete", side_effect=slow):
        job_scorer.score_jobs(JOBS, PROFILE)

    assert peak > 1


def _peak_concurrency() -> int:
    active = peak = 0
    lock = threading.Lock()

    def slow(*args, **kwargs):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.05)
        with lock:
            active -= 1
        return GOOD

    with patch.object(job_scorer, "complete", side_effect=slow):
        job_scorer.score_jobs(JOBS, PROFILE)
    return peak


def test_concurrency_stays_inside_the_free_tier():
    """Firing all 15 at once would trip the per-minute limit and fail most."""
    assert _peak_concurrency() <= job_scorer._MAX_CONCURRENT


def test_scoring_goes_one_at_a_time_while_on_the_fallback():
    """Measured: with the primary down, five at a time made a real run *slower*
    (13.5s a job against 4.3s sequential). The fallback's ceiling is tokens per
    minute, not requests, so parallelism just buys 429s and backoff."""
    with patch.object(job_scorer, "primary_is_available", return_value=False):
        assert _peak_concurrency() == 1


def test_scoring_goes_wide_while_the_primary_is_healthy():
    with patch.object(job_scorer, "primary_is_available", return_value=True):
        assert _peak_concurrency() > 1


def test_the_first_job_is_scored_alone_to_learn_which_provider_is_answering():
    """Deciding up front guesses: a fresh circuit breaker reports the primary
    as healthy, so a run would fan out five wide and only then discover
    everything was falling to the fallback. One job first settles it."""
    spans: list[tuple[float, float]] = []
    lock = threading.Lock()

    def slow(*args, **kwargs):
        started = time.monotonic()
        time.sleep(0.05)
        with lock:
            spans.append((started, time.monotonic()))
        return GOOD

    with patch.object(job_scorer, "complete", side_effect=slow), \
         patch.object(job_scorer, "primary_is_available", return_value=True):
        job_scorer.score_jobs(JOBS, PROFILE)

    spans.sort()
    probe_end = spans[0][1]
    # Nothing else may start until the probe has come back.
    assert all(start >= probe_end for start, _ in spans[1:])
    # And the rest still overlap each other.
    assert spans[2][0] < spans[1][1]


def test_every_job_still_comes_back():
    with patch.object(job_scorer, "complete", return_value=GOOD):
        scored = job_scorer.score_jobs(JOBS, PROFILE)

    assert len(scored) == len(JOBS)
    assert {j["title"] for j in scored} == {j["title"] for j in JOBS}


def test_results_are_still_ordered_best_first():
    scores = iter([json.dumps({"score": s, "reasoning": "r"}) for s in (30, 90, 60)])

    with patch.object(job_scorer, "complete", side_effect=lambda *a, **k: next(scores)):
        scored = job_scorer.score_jobs(JOBS[:3], PROFILE)

    assert [j["llm_score"] for j in scored] == [90, 60, 30]


def test_one_job_failing_does_not_take_down_the_others():
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] <= job_scorer._MAX_ATTEMPTS:      # first job burns its retries
            raise RuntimeError("rate limited")
        return GOOD

    with patch.object(job_scorer, "complete", side_effect=flaky):
        scored = job_scorer.score_jobs(JOBS[:4], PROFILE)

    assert len(scored) == 4
    assert sum(1 for j in scored if j["llm_score"] is None) == 1
    assert scored[-1]["llm_score"] is None             # the failure sorts last


def test_scoring_nothing_does_nothing():
    with patch.object(job_scorer, "complete") as c:
        assert job_scorer.score_jobs([], PROFILE) == []
    c.assert_not_called()
