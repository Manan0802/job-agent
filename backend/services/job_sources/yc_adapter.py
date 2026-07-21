"""Y Combinator startup jobs.

The Phase 2 plan called for `jwc20/waasuapi`, which logs into workatastartup
with real credentials and drives Selenium. That turned out to be unnecessary:
YC's public job pages embed their listings as JSON in the HTML, so this reads
them directly — no login, no browser, no stale dependency, and no exception to
the project's "no authenticated scraping" rule.

Coverage comes from several public filter pages because each returns a
different slice; there is no pagination to walk.
"""

import html
import json
import logging
import re
from datetime import datetime, timezone

import httpx

log = logging.getLogger(__name__)

BASE_URL = "https://www.ycombinator.com"
DEFAULT_PATHS = [
    "/jobs",
    "/jobs/role/eng",
    "/jobs/role/design",
    "/jobs/location/remote",
]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}
_PAGE_PAYLOAD = re.compile(r'data-page="(.*?)"><', re.S)


def _extract_postings(page_html: str) -> list[dict]:
    match = _PAGE_PAYLOAD.search(page_html)
    if not match:
        log.warning("YC page layout changed: no embedded job payload found")
        return []
    try:
        payload = json.loads(html.unescape(match.group(1)))
    except json.JSONDecodeError as exc:
        log.warning("YC embedded payload was not valid JSON: %s", exc)
        return []
    return payload.get("props", {}).get("jobPostings") or []


def _describe(posting: dict) -> str:
    """YC gives structured fields rather than prose, so build the text the
    matcher needs out of them."""
    bits = [
        posting.get("companyOneLiner"),
        f"Role: {posting.get('prettyRole')}" if posting.get("prettyRole") else None,
        f"Type: {posting.get('type')}" if posting.get("type") else None,
        f"Experience: {posting.get('minExperience')}" if posting.get("minExperience") else None,
        f"Salary: {posting.get('salaryRange')}" if posting.get("salaryRange") else None,
        f"Equity: {posting.get('equityRange')}" if posting.get("equityRange") else None,
        f"Visa: {posting.get('visa')}" if posting.get("visa") else None,
        f"Batch: {posting.get('companyBatchName')}" if posting.get("companyBatchName") else None,
    ]
    return " | ".join(b for b in bits if b)


def _normalize(posting: dict, fetched_at: str) -> dict:
    url = posting.get("url") or ""
    if url.startswith("/"):
        url = f"{BASE_URL}{url}"
    return {
        "title": posting.get("title"),
        "company": posting.get("companyName"),
        "location": posting.get("location"),
        "url": url or None,
        "description": _describe(posting),
        "date_posted": posting.get("createdAt"),
        "source_engine": "yc",
        "fetched_at": fetched_at,
    }


def fetch_yc_jobs(paths: list[str] | None = None) -> list[dict]:
    fetched_at = datetime.now(timezone.utc).isoformat()
    seen: set[str] = set()
    jobs: list[dict] = []

    for path in paths or DEFAULT_PATHS:
        try:
            resp = httpx.get(f"{BASE_URL}{path}", headers=_HEADERS, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            postings = _extract_postings(resp.text)
        except Exception as exc:
            log.warning("YC page %s failed: %s", path, exc)
            continue

        for posting in postings:
            posting_id = str(posting.get("id") or posting.get("url") or "")
            if posting_id in seen:
                continue
            seen.add(posting_id)
            jobs.append(_normalize(posting, fetched_at))

    return jobs
