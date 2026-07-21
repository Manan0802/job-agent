"""YC's job pages embed their listings as JSON in the public HTML, so no login,
Selenium, or Chromedriver is involved — see the note in yc_adapter.
"""

import html
import json
from unittest.mock import patch, MagicMock

from backend.services.job_sources import yc_adapter


def _page(jobs: list[dict]) -> MagicMock:
    payload = json.dumps({"component": "WaasLandingPage", "props": {"jobPostings": jobs}})
    resp = MagicMock()
    resp.text = f'<div id="app" data-page="{html.escape(payload, quote=True)}"><span></span></div>'
    resp.raise_for_status.return_value = None
    return resp


JOB = {
    "id": "71478",
    "title": "Backend Engineer",
    "companyName": "GoGoGrandparent",
    "location": "Remote",
    "url": "/companies/gogograndparent/jobs/abc-backend-engineer",
    "companyOneLiner": "Rides for seniors",
    "salaryRange": "$100K - $150K",
    "minExperience": "1+ years",
    "createdAt": "2026-07-01",
}


def test_parses_jobs_embedded_in_the_page():
    with patch.object(yc_adapter.httpx, "get", return_value=_page([JOB])):
        jobs = yc_adapter.fetch_yc_jobs(paths=["/jobs"])

    assert len(jobs) == 1
    job = jobs[0]
    assert job["title"] == "Backend Engineer"
    assert job["company"] == "GoGoGrandparent"
    assert job["location"] == "Remote"
    assert job["source_engine"] == "yc"
    assert job["fetched_at"]


def test_relative_job_links_become_absolute_urls():
    with patch.object(yc_adapter.httpx, "get", return_value=_page([JOB])):
        job = yc_adapter.fetch_yc_jobs(paths=["/jobs"])[0]
    assert job["url"].startswith("https://www.ycombinator.com/")
    assert job["url"].endswith("/abc-backend-engineer")


def test_description_carries_the_details_that_drive_matching():
    with patch.object(yc_adapter.httpx, "get", return_value=_page([JOB])):
        job = yc_adapter.fetch_yc_jobs(paths=["/jobs"])[0]
    assert "Rides for seniors" in job["description"]
    assert "1+ years" in job["description"]


def test_the_same_job_listed_under_two_filters_is_returned_once():
    with patch.object(yc_adapter.httpx, "get", return_value=_page([JOB])):
        jobs = yc_adapter.fetch_yc_jobs(paths=["/jobs", "/jobs/role/eng"])
    assert len(jobs) == 1


def test_one_failing_page_does_not_lose_the_others():
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("yc timed out")
        return _page([JOB])

    with patch.object(yc_adapter.httpx, "get", side_effect=flaky):
        jobs = yc_adapter.fetch_yc_jobs(paths=["/jobs", "/jobs/role/eng"])
    assert len(jobs) == 1


def test_a_layout_change_that_drops_the_payload_is_not_fatal():
    """YC could restructure the page; that should degrade to zero jobs, not crash."""
    resp = MagicMock()
    resp.text = "<html><body>no data-page here</body></html>"
    resp.raise_for_status.return_value = None
    with patch.object(yc_adapter.httpx, "get", return_value=resp):
        assert yc_adapter.fetch_yc_jobs(paths=["/jobs"]) == []


def test_no_credentials_are_ever_sent():
    with patch.object(yc_adapter.httpx, "get", return_value=_page([JOB])) as get:
        yc_adapter.fetch_yc_jobs(paths=["/jobs"])
    kwargs = get.call_args.kwargs
    assert "auth" not in kwargs
    assert "cookies" not in kwargs
    assert "Authorization" not in (kwargs.get("headers") or {})
