"""Finding people who could refer you, from public Google results.

This searches Google for public LinkedIn profiles — no login and no LinkedIn
API, which is what keeps it ToS-clean. LinkedIn de-indexed headlines and work
history in 2024, so a result reliably yields name, profile URL and current
employer (from the page title) and little else. That is enough: the user opens
the profile to decide.

Providers are tried in order of what they cost us. Serper's free grant is
one-time (2,500 searches) and SerpApi's resets every month (250), so Serper
leads and SerpApi is the permanent floor. When both are gone,
`manual_search_url` still gives the user a link to click.
"""

import logging
import re
from typing import Callable
from urllib.parse import urlencode

import httpx

from backend.config import get_settings
from backend.services.api_budget import can_spend, record_call

log = logging.getLogger(__name__)

_settings = get_settings()

SERPER_URL = "https://google.serper.dev/search"
SERPAPI_URL = "https://serpapi.com/search"

# Asking for more than 10 results costs Serper a second credit.
_RESULTS_PER_SEARCH = 10

_PROFILE_URL = re.compile(r"linkedin\.com/in/", re.IGNORECASE)
_TITLE_TAIL = re.compile(r"\s*[|\-–]\s*LinkedIn\s*$", re.IGNORECASE)


def _build_query(company: str, role: str | None, location: str | None) -> str:
    parts = ['site:linkedin.com/in', f'"{company}"']
    if role:
        parts.append(f'"{role}"')
    if location:
        parts.append(f'"{location}"')
    return " ".join(parts)


def _parse_result(result: dict) -> dict | None:
    """Turn one SERP hit into a contact.

    Titles look like "Asha Rao - SDE-2 - Zepto | LinkedIn", sometimes without
    the role, sometimes with no company at all.
    """
    url = (result.get("link") or "").strip()
    if not url or not _PROFILE_URL.search(url):
        return None

    title = _TITLE_TAIL.sub("", (result.get("title") or "").strip())
    segments = [s.strip() for s in re.split(r"\s+[-–|]\s+", title) if s.strip()]
    if not segments:
        return None

    name, *rest = segments
    return {
        "name": name,
        "current_role": rest[0] if len(rest) > 1 else None,
        "current_company": rest[-1] if rest else None,
        "linkedin_url": url,
        "headline": (result.get("snippet") or "").strip() or None,
        "degree_type": "2nd",   # a stranger until the CSV proves otherwise
        "source": "search",
    }


def _search_serper(query: str) -> list[dict]:
    response = httpx.post(
        SERPER_URL,
        headers={"X-API-KEY": _settings.serper_api_key, "Content-Type": "application/json"},
        json={"q": query, "num": _RESULTS_PER_SEARCH},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("organic") or []


def _search_serpapi(query: str) -> list[dict]:
    response = httpx.get(
        SERPAPI_URL,
        params={"q": query, "api_key": _settings.serpapi_api_key,
                "num": _RESULTS_PER_SEARCH, "engine": "google"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("organic_results") or []


def _providers() -> list[tuple[str, str, int, Callable[[str], list[dict]]]]:
    return [
        ("serper", _settings.serper_api_key, _settings.serper_monthly_cap, _search_serper),
        ("serpapi", _settings.serpapi_api_key, _settings.serpapi_monthly_cap, _search_serpapi),
    ]


def search_people(company: str, role: str | None = None,
                  location: str | None = None) -> list[dict]:
    """Search for people at `company`. Returns [] when nothing is configured or
    every budget is spent — the caller falls back to the CSV and manual link."""
    query = _build_query(company, role, location)

    for name, api_key, cap, search in _providers():
        if not api_key:
            continue
        if not can_spend(name, cap):
            log.info("%s budget exhausted this month; trying next provider", name)
            continue
        try:
            results = search(query)
        except Exception as exc:
            log.warning("people search via %s failed: %s", name, exc)
            continue

        record_call(name, cap)
        people = [p for p in (_parse_result(r) for r in results) if p]
        log.info("people search via %s -> %d profiles", name, len(people))
        return people

    log.info("no people-search provider available for %r", company)
    return []


def manual_search_url(company: str, role: str | None = None,
                      school: str | None = None) -> str:
    """A LinkedIn search the user can run themselves — free, always available."""
    keywords = " ".join(part for part in (company, role, school) if part)
    return "https://www.linkedin.com/search/results/people/?" + urlencode({"keywords": keywords})
