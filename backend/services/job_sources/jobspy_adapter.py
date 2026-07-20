"""JobSpy adapter — scrapes LinkedIn/Indeed/Glassdoor/Naukri/Google via public search.

No login is used here: JobSpy hits public listings only. See the Phase 2 plan's
login policy — LinkedIn deliberately stays on this public path.
"""

from datetime import datetime, timezone

import pandas as pd
from jobspy import scrape_jobs

DEFAULT_SITES = ["linkedin", "indeed", "glassdoor", "naukri", "google"]


def _clean(value) -> str | None:
    """DataFrame cells arrive as NaN/NaT for missing data — store None instead."""
    if value is None or pd.isna(value):
        return None
    return str(value)


def fetch_jobs(
    search_term: str,
    location: str = "India",
    sites: list[str] | None = None,
    results_wanted: int = 20,
    hours_old: int = 72,
) -> list[dict]:
    df = scrape_jobs(
        site_name=sites or DEFAULT_SITES,
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        country_indeed="india",
    )
    if df is None or len(df) == 0:
        return []
    fetched_at = datetime.now(timezone.utc).isoformat()
    return [
        {
            "title": _clean(row.get("title")),
            "company": _clean(row.get("company")),
            "location": _clean(row.get("location")),
            "url": _clean(row.get("job_url")),
            "description": _clean(row.get("description")),
            "date_posted": _clean(row.get("date_posted")),
            "source_engine": f"jobspy:{_clean(row.get('site')) or 'unknown'}",
            "fetched_at": fetched_at,
        }
        for row in df.to_dict("records")
    ]
