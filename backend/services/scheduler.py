"""Hunting on a schedule, so the app finds jobs without being opened.

Two rules shape this:

- It only alerts on jobs the user has not already been told about. A hunt
  re-finds the same listings every run, so alerting on all of them daily is how
  an alert gets muted.
- It is off until configured. Hunting on its own would spend the free tier
  without being asked.
"""

import asyncio
import logging
from datetime import datetime, timezone

from backend.agents.job_hunter_graph import run_hunt
from backend.config import get_settings
from backend.services.new_matches import claim_new_matches
from backend.services.notify import format_job_alert, send_telegram_alert
from backend.services.profile_store import load_profile

log = logging.getLogger(__name__)

_settings = get_settings()

# What the last run did, for the Settings view to show.
last_run: dict | None = None


def is_enabled() -> bool:
    return bool(_settings.hunt_search_term) and _settings.hunt_every_hours > 0


def run_scheduled_hunt() -> dict:
    """One scheduled hunt. Never raises: a bad night must not stop tomorrow's."""
    global last_run
    started = datetime.now(timezone.utc).isoformat()

    profile = load_profile()
    if profile is None:
        last_run = {"at": started, "skipped": "No resume uploaded yet"}
        return last_run

    try:
        result = run_hunt(
            profile,
            search_term=_settings.hunt_search_term,
            location=_settings.hunt_location,
            top_n=_settings.hunt_top_n,
            notify=False,   # only new matches are worth a message
        )
    except Exception as exc:
        log.warning("scheduled hunt failed: %s", exc)
        last_run = {"at": started, "error": str(exc)}
        return last_run

    total_found = result.get("total_found", 0)
    fresh = claim_new_matches(min_score=_settings.alert_min_score)

    alerted = False
    if fresh:
        alerted = send_telegram_alert(format_job_alert(fresh, total_found))

    log.info("scheduled hunt: %d found, %d new", total_found, len(fresh))
    last_run = {
        "at": started, "total_found": total_found,
        "new_matches": len(fresh), "alerted": alerted,
    }
    return last_run


async def run_forever() -> None:
    """Hunt every `hunt_every_hours`, starting one interval from now.

    It waits first rather than hunting at startup: restarting the server is not
    a request to hunt, and during development that would be every reload.
    """
    interval = _settings.hunt_every_hours * 3600
    log.info("scheduled hunting on, every %dh", _settings.hunt_every_hours)
    while True:
        await asyncio.sleep(interval)
        # In a thread: a hunt takes minutes and would block every request.
        await asyncio.to_thread(run_scheduled_hunt)
