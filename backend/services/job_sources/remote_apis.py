"""Free remote-job APIs — no scraping, no keys, no login. Public JSON endpoints only.

Each fetcher normalizes to the same dict shape the jobspy adapter produces, so
downstream dedup/scoring treats every source identically.
"""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

log = logging.getLogger(__name__)

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
REMOTEOK_URL = "https://remoteok.com/api"
ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"
HIMALAYAS_URL = "https://himalayas.app/jobs/api"
JOBICY_URL = "https://jobicy.com/api/v2/remote-jobs"

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; job-agent/1.0)"}


def _get(url: str) -> Any:
    resp = httpx.get(url, timeout=30, headers=_HEADERS, follow_redirects=True)
    resp.raise_for_status()
    return resp.json()


def _row(*, title, company, location, url, description, date_posted, source: str) -> dict:
    return {
        "title": str(title) if title else None,
        "company": str(company) if company else None,
        "location": str(location) if location else None,
        "url": str(url) if url else None,
        "description": str(description) if description else None,
        "date_posted": str(date_posted) if date_posted else None,
        "source_engine": source,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_remotive() -> list[dict]:
    data = _get(REMOTIVE_URL)
    return [
        _row(
            title=j.get("title"), company=j.get("company_name"),
            location=j.get("candidate_required_location"), url=j.get("url"),
            description=j.get("description"), date_posted=j.get("publication_date"),
            source="remotive",
        )
        for j in data.get("jobs", [])
    ]


def fetch_remoteok() -> list[dict]:
    data = _get(REMOTEOK_URL)
    # RemoteOK's first list element is a legal notice, not a job — it has no "position".
    return [
        _row(
            title=j.get("position"), company=j.get("company"), location=j.get("location"),
            url=j.get("url"), description=j.get("description"), date_posted=j.get("date"),
            source="remoteok",
        )
        for j in data
        if isinstance(j, dict) and j.get("position")
    ]


def fetch_arbeitnow() -> list[dict]:
    data = _get(ARBEITNOW_URL)
    return [
        _row(
            title=j.get("title"), company=j.get("company_name"), location=j.get("location"),
            url=j.get("url"), description=j.get("description"), date_posted=j.get("created_at"),
            source="arbeitnow",
        )
        for j in data.get("data", [])
    ]


def fetch_himalayas() -> list[dict]:
    data = _get(HIMALAYAS_URL)
    jobs = []
    for j in data.get("jobs", []):
        locations = j.get("locationRestrictions") or []
        jobs.append(_row(
            title=j.get("title"), company=j.get("companyName"),
            location=", ".join(locations) if locations else None,
            url=j.get("applicationLink"), description=j.get("description"),
            date_posted=j.get("pubDate"), source="himalayas",
        ))
    return jobs


def fetch_jobicy() -> list[dict]:
    data = _get(JOBICY_URL)
    return [
        _row(
            title=j.get("jobTitle"), company=j.get("companyName"), location=j.get("jobGeo"),
            url=j.get("url"), description=j.get("jobDescription"), date_posted=j.get("pubDate"),
            source="jobicy",
        )
        for j in data.get("jobs", [])
    ]


def fetch_all_remote() -> list[dict]:
    """Run every free source. A dead source is logged and skipped, never fatal."""
    jobs: list[dict] = []
    for fetcher in (fetch_remotive, fetch_remoteok, fetch_arbeitnow, fetch_himalayas, fetch_jobicy):
        try:
            jobs.extend(fetcher())
        except Exception as exc:
            log.warning("remote job source %s failed: %s", fetcher.__name__, exc)
    return jobs
