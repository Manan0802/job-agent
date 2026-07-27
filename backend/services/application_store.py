"""The application pipeline.

Losing track of an application is the failure this module exists to prevent,
so every stage change also sets when the user should next check on it — and
only a finished application stops asking.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from backend.db.database import get_session
from backend.db.models import ApplicationRow

PIPELINE_STAGES = (
    "saved",
    "applied",
    "referral_pending",
    "interview_scheduled",
    "interview_done",
    "offer_received",
    "accepted",
    "rejected",
)

FINAL_STAGES = frozenset({"accepted", "rejected"})

# How long to leave each stage alone before it is worth a nudge.
_FOLLOW_UP_DAYS = {
    "saved": 3,                 # you meant to apply
    "applied": 6,               # no reply yet
    "referral_pending": 5,      # your referrer has not come back
    "interview_scheduled": 1,   # prep, and confirm the slot
    "interview_done": 2,        # thank-you, then chase
    "offer_received": 3,        # they are waiting on you
}

# The date a stage is really about, filled in when you get there.
_STAGE_DATE_FIELD = {
    "applied": "applied_date",
    "interview_scheduled": "interview_date",
    "offer_received": "offer_date",
}

_FIELDS = (
    "job_id", "company_name", "role_title", "apply_url", "source", "applied_via",
    "referral_contact_id", "status", "applied_date", "interview_date", "offer_date",
    "offer_amount", "offer_currency", "notes", "follow_up_due", "created_at",
    "last_updated",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _next_follow_up(status: str) -> str | None:
    days = _FOLLOW_UP_DAYS.get(status)
    return (_now() + timedelta(days=days)).isoformat() if days else None


def track_job(job: dict, applied_via: str = "direct",
              referral_contact_id: str | None = None) -> str:
    """Start tracking a job, or return the existing application untouched.

    Re-saving a job you have already progressed must never rewind it.
    """
    with get_session() as session:
        existing = session.scalars(
            select(ApplicationRow).where(ApplicationRow.job_id == job.get("id"))
        ).first()
        if existing is not None:
            return existing.id

        now = _now().isoformat()
        row = ApplicationRow(
            id=str(uuid.uuid4()),
            job_id=job.get("id"),
            company_name=job.get("company"),
            role_title=job.get("title"),
            apply_url=job.get("url"),
            source=job.get("source_engine"),
            applied_via=applied_via,
            referral_contact_id=referral_contact_id,
            status="saved",
            follow_up_due=_next_follow_up("saved"),
            created_at=now,
            last_updated=now,
        )
        session.add(row)
        session.commit()
        return row.id


def _get(session, application_id: str) -> ApplicationRow:
    row = session.get(ApplicationRow, application_id)
    if row is None:
        raise KeyError(f"no application with id {application_id!r}")
    return row


def move_stage(application_id: str, status: str) -> None:
    if status not in PIPELINE_STAGES:
        raise ValueError(
            f"unknown stage {status!r} — expected one of {', '.join(PIPELINE_STAGES)}"
        )

    with get_session() as session:
        row = _get(session, application_id)
        row.status = status
        row.last_updated = _now().isoformat()

        date_field = _STAGE_DATE_FIELD.get(status)
        if date_field and getattr(row, date_field) is None:
            setattr(row, date_field, _now().isoformat())

        row.follow_up_due = None if status in FINAL_STAGES else _next_follow_up(status)
        session.commit()


def add_note(application_id: str, note: str) -> None:
    """Notes build up a history, so a new one is appended rather than replacing."""
    with get_session() as session:
        row = _get(session, application_id)
        stamp = _now().strftime("%Y-%m-%d")
        entry = f"[{stamp}] {note}"
        row.notes = f"{row.notes}\n{entry}" if row.notes else entry
        row.last_updated = _now().isoformat()
        session.commit()


def record_offer(application_id: str, amount: int, currency: str = "INR") -> None:
    with get_session() as session:
        row = _get(session, application_id)
        row.offer_amount = amount
        row.offer_currency = currency
        row.last_updated = _now().isoformat()
        session.commit()


def get_application(application_id: str) -> dict | None:
    with get_session() as session:
        row = session.get(ApplicationRow, application_id)
        return None if row is None else {"id": row.id, **{f: getattr(row, f) for f in _FIELDS}}


def load_applications(status: str | None = None) -> list[dict]:
    statement = select(ApplicationRow)
    if status:
        statement = statement.where(ApplicationRow.status == status)

    with get_session() as session:
        rows = session.scalars(statement).all()

    applications = [{"id": row.id, **{f: getattr(row, f) for f in _FIELDS}} for row in rows]
    applications.sort(key=lambda a: a["last_updated"] or "", reverse=True)
    return applications
