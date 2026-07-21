"""Telegram job alerts.

Notification is the last step of a hunt, so a missing token or a Telegram
outage reports failure rather than throwing away a completed run.
"""

import logging

import httpx

from backend.config import get_settings

log = logging.getLogger(__name__)

_settings = get_settings()

_MAX_LISTED_JOBS = 10


def send_telegram_alert(message: str) -> bool:
    """Return whether the alert actually went out."""
    token = _settings.telegram_bot_token
    chat_id = _settings.telegram_chat_id
    if not token or not chat_id:
        log.info("telegram not configured; skipping alert")
        return False

    try:
        resp = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "disable_web_page_preview": True},
            timeout=20,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        log.warning("telegram alert failed: %s", exc)
        return False


def format_job_alert(jobs: list[dict], total_found: int) -> str:
    if not jobs:
        return f"Job hunt finished: {total_found} jobs found, none matched well enough."

    lines = [f"{len(jobs)} strong matches out of {total_found} jobs found:", ""]
    for job in jobs[:_MAX_LISTED_JOBS]:
        score = job.get("llm_score")
        score_label = f"{score:.0f}" if score is not None else "unscored"
        lines.append(f"[{score_label}] {job.get('title')} @ {job.get('company')}")
        if job.get("url"):
            lines.append(job["url"])
        lines.append("")
    return "\n".join(lines).strip()
