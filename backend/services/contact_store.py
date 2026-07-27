"""Persisting referral contacts.

Saving is an upsert because a hunt re-runs against the same company, and it
deliberately leaves `outreach_status` alone: that column belongs to the
outreach flow, so a later hunt must not reset someone you already messaged
back to "pending".
"""

from sqlalchemy import select

from backend.db.database import get_session
from backend.db.models import ContactRow

_COLUMNS = (
    "target_company", "name", "linkedin_url", "current_role", "current_company",
    "location", "education", "degree_type", "warmth_score", "warmth_reasons",
    "email", "source", "created_at",
)


def save_contacts(contacts: list[dict]) -> None:
    if not contacts:
        return
    with get_session() as session:
        for contact in contacts:
            row = session.get(ContactRow, contact["id"])
            if row is None:
                row = ContactRow(id=contact["id"])
                session.add(row)
            for column in _COLUMNS:
                value = contact.get(column)
                if value is not None:
                    setattr(row, column, value)
            status = contact.get("outreach_status")
            if status:
                row.outreach_status = status
        session.commit()


def get_contact(contact_id: str) -> dict | None:
    with get_session() as session:
        row = session.get(ContactRow, contact_id)
        if row is None:
            return None
        return {"id": row.id, "outreach_status": row.outreach_status,
                **{column: getattr(row, column) for column in _COLUMNS}}


def set_outreach_status(contact_id: str, status: str) -> None:
    with get_session() as session:
        row = session.get(ContactRow, contact_id)
        if row is not None:
            row.outreach_status = status
            session.commit()


def load_contacts(company: str | None = None) -> list[dict]:
    """Warmest first."""
    statement = select(ContactRow)
    if company:
        statement = statement.where(ContactRow.target_company == company)

    with get_session() as session:
        rows = session.scalars(statement).all()

    contacts = [
        {"id": row.id, "outreach_status": row.outreach_status,
         **{column: getattr(row, column) for column in _COLUMNS}}
        for row in rows
    ]
    contacts.sort(key=lambda c: -(c["warmth_score"] or 0))
    return contacts
