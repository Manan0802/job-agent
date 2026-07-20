from unittest.mock import patch
from backend.services.job_sources import remote_apis

REMOTIVE = {"jobs": [{
    "title": "Backend Engineer", "company_name": "Remotive Co",
    "candidate_required_location": "Worldwide", "url": "https://remotive.com/j/1",
    "description": "Build APIs", "publication_date": "2026-07-01T10:00:00",
}]}

# RemoteOK returns a top-level list whose FIRST element is a legal notice, not a job.
REMOTEOK = [
    {"last_updated": "2026-07-13", "legal": "Scraping this API is fine"},
    {"position": "Data Engineer", "company": "RemoteOK Co", "location": "Remote",
     "url": "https://remoteok.com/j/2", "description": "Pipelines", "date": "2026-07-02"},
]

ARBEITNOW = {"data": [{
    "title": "Fullstack Dev", "company_name": "Arbeit Co", "location": "Berlin",
    "url": "https://arbeitnow.com/j/3", "description": "Ship features", "created_at": 1783000000,
}]}

HIMALAYAS = {"jobs": [{
    "title": "ML Engineer", "companyName": "Himalayas Co",
    "locationRestrictions": ["India", "Singapore"], "applicationLink": "https://himalayas.app/j/4",
    "description": "Train models", "pubDate": "2026-07-03",
}]}

JOBICY = {"jobs": [{
    "jobTitle": "AI Engineer", "companyName": "Jobicy Co", "jobGeo": "Anywhere",
    "url": "https://jobicy.com/j/5", "jobDescription": "LLM work", "pubDate": "2026-07-04",
}]}


def test_fetch_remotive_normalizes():
    with patch.object(remote_apis, "_get", return_value=REMOTIVE):
        jobs = remote_apis.fetch_remotive()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Backend Engineer"
    assert jobs[0]["company"] == "Remotive Co"
    assert jobs[0]["location"] == "Worldwide"
    assert jobs[0]["url"] == "https://remotive.com/j/1"
    assert jobs[0]["source_engine"] == "remotive"
    assert jobs[0]["fetched_at"]


def test_fetch_remoteok_skips_legal_notice_entry():
    with patch.object(remote_apis, "_get", return_value=REMOTEOK):
        jobs = remote_apis.fetch_remoteok()
    assert len(jobs) == 1                      # legal-notice element dropped
    assert jobs[0]["title"] == "Data Engineer"
    assert jobs[0]["company"] == "RemoteOK Co"
    assert jobs[0]["source_engine"] == "remoteok"


def test_fetch_arbeitnow_normalizes():
    with patch.object(remote_apis, "_get", return_value=ARBEITNOW):
        jobs = remote_apis.fetch_arbeitnow()
    assert jobs[0]["title"] == "Fullstack Dev"
    assert jobs[0]["date_posted"] == "1783000000"
    assert jobs[0]["source_engine"] == "arbeitnow"


def test_fetch_himalayas_joins_location_list():
    with patch.object(remote_apis, "_get", return_value=HIMALAYAS):
        jobs = remote_apis.fetch_himalayas()
    assert jobs[0]["company"] == "Himalayas Co"
    assert jobs[0]["location"] == "India, Singapore"
    assert jobs[0]["url"] == "https://himalayas.app/j/4"


def test_fetch_jobicy_normalizes():
    with patch.object(remote_apis, "_get", return_value=JOBICY):
        jobs = remote_apis.fetch_jobicy()
    assert jobs[0]["title"] == "AI Engineer"
    assert jobs[0]["description"] == "LLM work"
    assert jobs[0]["source_engine"] == "jobicy"


def test_fetch_all_remote_survives_one_source_failing():
    """One dead API must not take down the whole ingest step."""
    def flaky(url: str):
        if "remoteok" in url:
            raise ConnectionError("remoteok is down")
        return REMOTIVE if "remotive" in url else {"jobs": [], "data": []}

    with patch.object(remote_apis, "_get", side_effect=flaky):
        jobs = remote_apis.fetch_all_remote()
    assert any(j["source_engine"] == "remotive" for j in jobs)
    assert not any(j["source_engine"] == "remoteok" for j in jobs)
