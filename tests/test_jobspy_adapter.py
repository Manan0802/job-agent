import pandas as pd
from unittest.mock import patch
from backend.services.job_sources import jobspy_adapter

FAKE_ROWS = [
    {
        "site": "linkedin",
        "title": "SDE-1",
        "company": "Zepto",
        "location": "Mumbai, India",
        "job_url": "https://linkedin.com/jobs/1",
        "description": "Build backend systems",
        "date_posted": "2026-07-01",
    },
    {
        "site": "naukri",
        "title": "AI Engineer",
        "company": "IndiaMART",
        "location": "Noida, India",
        "job_url": "https://naukri.com/jobs/2",
        "description": "Ship LLM features",
        "date_posted": "2026-07-02",
    },
]


def test_fetch_jobs_normalizes_rows():
    with patch.object(jobspy_adapter, "scrape_jobs", return_value=pd.DataFrame(FAKE_ROWS)) as sj:
        jobs = jobspy_adapter.fetch_jobs("software engineer", location="India")
    assert len(jobs) == 2
    first = jobs[0]
    assert first["title"] == "SDE-1"
    assert first["company"] == "Zepto"
    assert first["location"] == "Mumbai, India"
    assert first["url"] == "https://linkedin.com/jobs/1"
    assert first["description"] == "Build backend systems"
    assert first["date_posted"] == "2026-07-01"
    assert first["source_engine"] == "jobspy:linkedin"
    assert first["fetched_at"]
    assert jobs[1]["source_engine"] == "jobspy:naukri"
    _, kwargs = sj.call_args
    assert kwargs["search_term"] == "software engineer"
    assert kwargs["location"] == "India"


def test_fetch_jobs_returns_empty_when_no_results():
    with patch.object(jobspy_adapter, "scrape_jobs", return_value=pd.DataFrame()):
        assert jobspy_adapter.fetch_jobs("nothing here") == []


def test_fetch_jobs_converts_missing_values_to_none():
    rows = [{
        "site": "indeed",
        "title": "Backend Dev",
        "company": "Acme",
        "location": None,
        "job_url": "https://indeed.com/jobs/3",
        "description": float("nan"),
        "date_posted": None,
    }]
    with patch.object(jobspy_adapter, "scrape_jobs", return_value=pd.DataFrame(rows)):
        jobs = jobspy_adapter.fetch_jobs("backend")
    assert jobs[0]["location"] is None
    assert jobs[0]["description"] is None
    assert jobs[0]["date_posted"] is None
