"""What the tracker is for: what has gone stale, and whether any of this works.

The response rate treats a rejection as a reply — the user marks something
rejected when they actually hear back, and leaves a job that ghosted them
sitting in "applied". Jobs that were only ever saved are excluded entirely,
since never applying is not the same as being ignored.
"""

from collections import Counter
from datetime import datetime, timezone

from backend.services.application_store import (
    FINAL_STAGES,
    PIPELINE_STAGES,
    load_applications,
)

# Reaching any of these means somebody on the other side replied.
_RESPONDED_STAGES = frozenset(
    {"referral_pending", "interview_scheduled", "interview_done",
     "offer_received", "accepted", "rejected"}
)

_ACTIONS = {
    "saved": "You saved this but never applied — still interested?",
    "applied": "No reply yet — send a follow-up?",
    "referral_pending": "Your referrer hasn't come back — worth a gentle nudge?",
    "interview_scheduled": "Interview coming up — confirm the slot and prep.",
    "interview_done": "Send a thank-you note while it's still fresh.",
    "offer_received": "They're waiting on your answer — decide on this offer.",
}


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def due_reminders() -> list[dict]:
    """Applications the user has let go past their follow-up date, most
    neglected first."""
    now = datetime.now(timezone.utc)
    reminders = []

    for application in load_applications():
        if application["status"] in FINAL_STAGES:
            continue
        due = _parse(application["follow_up_due"])
        if due is None or due > now:
            continue
        reminders.append({
            **application,
            "days_overdue": (now - due).days,
            "action": _ACTIONS.get(application["status"], "Check where this stands."),
        })

    reminders.sort(key=lambda r: -r["days_overdue"])
    return reminders


def _rate(responded: int, applied: int) -> float:
    return round(100.0 * responded / applied, 1) if applied else 0.0


def pipeline_stats() -> dict:
    applications = load_applications()
    by_stage = Counter(a["status"] for a in applications)

    # "Applied" means it got at least that far, not that it is sitting there now.
    reached_applied = [
        a for a in applications
        if a["status"] != "saved" and a["applied_date"] is not None
    ]
    responded = [a for a in reached_applied if a["status"] in _RESPONDED_STAGES]

    by_source: dict[str, dict] = {}
    for application in reached_applied:
        source = application["source"] or "unknown"
        bucket = by_source.setdefault(source, {"applied": 0, "responded": 0})
        bucket["applied"] += 1
        if application["status"] in _RESPONDED_STAGES:
            bucket["responded"] += 1
    for bucket in by_source.values():
        bucket["response_rate"] = _rate(bucket["responded"], bucket["applied"])

    best_source = max(
        by_source.items(),
        key=lambda item: (item[1]["response_rate"], item[1]["applied"]),
        default=(None, None),
    )[0]

    return {
        "total": len(applications),
        "by_stage": {stage: by_stage.get(stage, 0) for stage in PIPELINE_STAGES},
        "applied": len(reached_applied),
        "responded": len(responded),
        "response_rate": _rate(len(responded), len(reached_applied)),
        "active": sum(1 for a in applications if a["status"] not in FINAL_STAGES),
        "offers": by_stage.get("offer_received", 0) + by_stage.get("accepted", 0),
        "by_source": by_source,
        "best_source": best_source,
    }
