"""Handing an approved message to the user to send.

Deliberately no sender lives here. Automating LinkedIn DMs is what got AIHawk
pulled, and the account that would be banned is the user's own — the same
account they are job hunting with. So every path ends in a link they click and
a message they send themselves.
"""

from urllib.parse import quote

from backend.schemas.outreach import OutreachDraft


def build_send_link(draft: OutreachDraft, contact: dict) -> dict:
    """Return where to go, what to paste, and what to do."""
    email = (contact.get("email") or "").strip()
    profile = (contact.get("linkedin_url") or "").strip() or None
    name = contact.get("name") or "them"

    if draft.channel == "email" and email:
        query = "&".join([
            f"subject={quote(draft.subject or '')}",
            f"body={quote(draft.message)}",
        ])
        return {
            "action": "open_mail_client",
            "url": f"mailto:{email}?{query}",
            "copy_text": draft.message,
            "instructions": f"Opens your mail client with the message to {name} "
                            "ready. Read it once, then send.",
        }

    if profile:
        instructions = (f"Open {name}'s profile, hit Message, and paste the text. "
                        "Edit anything that does not sound like you.")
    else:
        instructions = (f"No profile link for {name} — search for them on LinkedIn, "
                        "then paste the text.")

    return {
        "action": "open_and_paste",
        "url": profile,
        "copy_text": draft.message,
        "instructions": instructions,
    }
