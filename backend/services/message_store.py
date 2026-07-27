"""Outreach messages and their review lifecycle.

The rule this module enforces: the user is always the one who sends. A draft
becomes `approved` when they say so and `sent` only after they have actually
sent it. Anything already sent is immutable history — redrafting for that
contact creates a new message rather than overwriting the record.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from backend.db.database import get_session
from backend.db.models import MessageRow

_FIELDS = (
    "contact_id", "job_id", "message_type", "channel", "subject",
    "body", "tone", "personalization",
)

_LIVE_STATUSES = ("draft", "approved")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_message(message: dict) -> str:
    """Store a draft, replacing any un-sent draft for the same contact.

    Regenerating should not pile up stale drafts, but it must never disturb a
    message the user already sent.
    """
    with get_session() as session:
        existing = session.scalars(
            select(MessageRow)
            .where(MessageRow.contact_id == message.get("contact_id"))
            .where(MessageRow.status.in_(_LIVE_STATUSES))
        ).first()

        row = existing or MessageRow(id=str(uuid.uuid4()), created_at=_now())
        for field in _FIELDS:
            setattr(row, field, message.get(field))
        row.status = "draft"
        row.sent_at = None
        if existing is None:
            session.add(row)
        session.commit()
        return row.id


def _get(session, message_id: str) -> MessageRow:
    row = session.get(MessageRow, message_id)
    if row is None:
        raise KeyError(f"no outreach message with id {message_id!r}")
    return row


def update_message(message_id: str, **changes) -> None:
    """Apply the user's edits. Editing an approved message returns it to draft,
    so nothing goes out under an approval that was given for different words."""
    with get_session() as session:
        row = _get(session, message_id)
        for field, value in changes.items():
            if field in _FIELDS:
                setattr(row, field, value)
        if row.status == "approved":
            row.status = "draft"
        session.commit()


def _set_status(message_id: str, status: str, sent: bool = False) -> None:
    with get_session() as session:
        row = _get(session, message_id)
        row.status = status
        if sent:
            row.sent_at = _now()
        session.commit()


def approve_message(message_id: str) -> None:
    _set_status(message_id, "approved")


def mark_sent(message_id: str) -> None:
    """Record that the user sent it — this does not send anything."""
    _set_status(message_id, "sent", sent=True)


def skip_message(message_id: str) -> None:
    _set_status(message_id, "skipped")


def load_messages(contact_id: str | None = None, status: str | None = None) -> list[dict]:
    statement = select(MessageRow)
    if contact_id:
        statement = statement.where(MessageRow.contact_id == contact_id)
    if status:
        statement = statement.where(MessageRow.status == status)

    with get_session() as session:
        rows = session.scalars(statement).all()

    return [
        {"id": row.id, "status": row.status, "created_at": row.created_at,
         "sent_at": row.sent_at, **{f: getattr(row, f) for f in _FIELDS}}
        for row in rows
    ]
