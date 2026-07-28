"""Draft, review and hand off outreach messages.

Nothing in here sends. `POST /{id}/sent` records that the user sent it
themselves, which is also what tells the tracker this contact is no longer
waiting.
"""

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.agents.outreach_drafter import draft_message
from backend.schemas.outreach import OutreachDraft
from backend.services.contact_store import get_contact, set_outreach_status
from backend.services.job_store import get_job
from backend.services.message_store import (
    approve_message,
    load_messages,
    mark_sent,
    save_message,
    skip_message,
    update_message,
)
from backend.services.profile_store import load_profile
from backend.services.send_links import build_send_link

router = APIRouter(prefix="/api/v1/outreach", tags=["outreach"])


class DraftRequest(BaseModel):
    contact_id: str
    job_id: str | None = None
    message_type: str | None = None


class EditRequest(BaseModel):
    body: str | None = None
    subject: str | None = None


def _require_message(message_id: str) -> dict:
    messages = [m for m in load_messages() if m["id"] == message_id]
    if not messages:
        raise HTTPException(status_code=404, detail=f"No outreach message {message_id}")
    return messages[0]


def _require_contact(contact_id: str) -> dict:
    contact = get_contact(contact_id)
    if contact is None:
        raise HTTPException(
            status_code=404,
            detail=f"No contact {contact_id} — run /api/v1/referrals/find first",
        )
    return contact


def _with_send_link(message: dict) -> dict:
    """Attach where to go and what to paste, so the UI never has to rebuild it."""
    contact = get_contact(message["contact_id"]) or {}
    draft = OutreachDraft(
        message=message["body"] or "",
        subject=message["subject"],
        tone=message["tone"] or "professional",
        message_type=message["message_type"] or "cold_intro",
        channel=message["channel"] or "linkedin_dm",
    )
    return {
        **message,
        "contact_name": contact.get("name"),
        "send": build_send_link(draft, contact),
    }


@router.post("/draft")
def draft(request: DraftRequest):
    """Write a message for this contact. It is saved as a draft for review."""
    profile = load_profile()
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail="No profile yet — upload a resume at /api/v1/resume/upload first",
        )
    contact = _require_contact(request.contact_id)

    reasons = contact.get("warmth_reasons")
    if isinstance(reasons, str):
        try:
            contact = {**contact, "warmth_reasons": json.loads(reasons)}
        except json.JSONDecodeError:
            contact = {**contact, "warmth_reasons": [reasons]}

    # Without the job the message can only guess at the role — a live draft
    # once offered to apply for an SDE-1 opening when the role was SDE-2.
    job = get_job(request.job_id) if request.job_id else None
    written = draft_message(contact, profile, job=job, message_type=request.message_type)
    message_id = save_message({
        "contact_id": request.contact_id,
        "job_id": request.job_id,
        "message_type": written.message_type,
        "channel": written.channel,
        "subject": written.subject,
        "body": written.message,
        "tone": written.tone,
        "personalization": json.dumps(written.personalization_elements),
    })
    # So the referrals list shows you already wrote to them. Only from
    # "pending", or a follow-up draft would make a sent contact look untouched.
    if contact.get("outreach_status") == "pending":
        set_outreach_status(request.contact_id, "drafted")
    return _with_send_link(_require_message(message_id))


@router.post("/{message_id}/follow-up")
def follow_up(message_id: str):
    """Nudge a message that got no reply, without repeating the pitch."""
    original = _require_message(message_id)
    if original["status"] != "sent":
        raise HTTPException(
            status_code=400,
            detail="You can only follow up on a message you've already sent.",
        )

    profile = load_profile()
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail="No profile yet — upload a resume at /api/v1/resume/upload first",
        )
    contact = _require_contact(original["contact_id"])

    written = draft_message(
        contact,
        profile,
        message_type="followup",
        previous_message=original["body"],
    )
    new_id = save_message({
        "contact_id": original["contact_id"],
        "job_id": original["job_id"],
        "message_type": written.message_type,
        "channel": written.channel,
        "subject": written.subject,
        "body": written.message,
        "tone": written.tone,
        "personalization": json.dumps(written.personalization_elements),
    })
    return _with_send_link(_require_message(new_id))


@router.get("")
def list_outreach(contact_id: str | None = None, status: str | None = None):
    messages = [_with_send_link(m) for m in load_messages(contact_id=contact_id, status=status)]
    return {"count": len(messages), "messages": messages}


@router.put("/{message_id}")
def edit(message_id: str, request: EditRequest):
    _require_message(message_id)
    changes = {k: v for k, v in request.model_dump().items() if v is not None}
    update_message(message_id, **changes)
    return _with_send_link(_require_message(message_id))


@router.post("/{message_id}/approve")
def approve(message_id: str):
    """Mark it ready to go. The user still sends it themselves."""
    _require_message(message_id)
    approve_message(message_id)
    return _with_send_link(_require_message(message_id))


@router.post("/{message_id}/sent")
def record_sent(message_id: str):
    """Record that the user has sent this message."""
    message = _require_message(message_id)
    mark_sent(message_id)
    if message["contact_id"]:
        set_outreach_status(message["contact_id"], "sent")
    return _with_send_link(_require_message(message_id))


@router.post("/{message_id}/skip")
def skip(message_id: str):
    message = _require_message(message_id)
    skip_message(message_id)
    if message["contact_id"]:
        set_outreach_status(message["contact_id"], "skipped")
    return _with_send_link(_require_message(message_id))
