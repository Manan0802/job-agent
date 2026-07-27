"""Writing the outreach message.

This is the part the user's reputation rides on. The message goes out under
their name to a real person who might become a colleague, so the prompt is
built to keep it short, specific and honest — and never to invent credentials
the user does not have.

Nothing here sends anything. The draft goes to the user for review.
"""

import json
import logging

from backend.llm.router import complete
from backend.schemas.outreach import OutreachDraft
from backend.schemas.profile import Profile

log = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
# A DM is a few hundred words; reserving more throttles Groq, which counts
# max_tokens toward its per-minute admission budget.
_DRAFT_MAX_TOKENS = 1500

MESSAGE_TYPES: dict[str, dict] = {
    "referral_request": {
        "channel": "linkedin_dm", "max_words": 200,
        "intent": "ask this person to refer you for a specific role at their company",
    },
    "alumni_dm": {
        "channel": "linkedin_dm", "max_words": 180,
        "intent": "open on the college you share, then ask this fellow alum to "
                  "refer you for the role",
    },
    "cold_intro": {
        "channel": "linkedin_dm", "max_words": 150,
        "intent": "introduce yourself to someone you share no history with and "
                  "ask whether they would refer you",
    },
    "email_outreach": {
        "channel": "email", "max_words": 250,
        "intent": "email this person to ask for a referral for the role",
    },
    "followup": {
        "channel": "linkedin_dm", "max_words": 90,
        "intent": "gently bump a message that got no reply, without repeating the pitch",
    },
    "thank_you": {
        "channel": "linkedin_dm", "max_words": 90,
        "intent": "thank someone who referred you",
    },
}

SYSTEM_PROMPT = (
    "You write short, warm, genuine outreach messages for a job seeker. "
    "Return ONLY a valid JSON object — no preamble, no markdown fences.\n\n"
    "TONE:\n"
    "- Warm and human, never corporate or stiff.\n"
    "- Peer-to-peer with people at a similar level; a little more formal with "
    "someone clearly senior.\n"
    "- Never sycophantic. Do not flatter the recipient or praise their work.\n"
    "- People skim DMs, so keep it tight.\n\n"
    "CONTENT:\n"
    "- Open with ONE genuine shared connection point, drawn from the reasons "
    "this contact was picked. Do not stack several.\n"
    "- Introduce the sender in at most two sentences.\n"
    "- Make the ask clear and specific.\n"
    "- Give them an easy out — 'no pressure', 'totally understand if not'.\n"
    "- Close with one specific next step, not a vague 'let me know'.\n"
    "- Do not offer or attach a resume in a first message.\n"
    "- A DM is a chat, not a letter: no email sign-off. End on the closing "
    "line, or at most a dash and the first name.\n\n"
    "HONESTY: use only facts present in the sender profile below. Never invent "
    "employers, titles, projects, dates or skills, and never overstate them.\n\n"
    "Return exactly:\n"
    "{\n"
    '  "subject": str or null (null for a DM),\n'
    '  "message": str,\n'
    '  "tone": "casual" | "professional" | "formal",\n'
    '  "personalization_elements": [str]\n'
    "}"
)


def pick_message_type(contact: dict) -> str:
    """Choose the opener that matches the real relationship."""
    reasons = " ".join(contact.get("warmth_reasons") or []).lower()
    if "alumni" in reasons:
        return "alumni_dm"
    if (contact.get("degree_type") or "").startswith("1"):
        return "referral_request"
    return "cold_intro"


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def _sender_summary(profile: Profile) -> str:
    s = profile.skills
    skills = [*s.languages, *s.frameworks, *s.ai_ml, *s.tools, *s.databases]
    roles = [f"{e.role} at {e.company}" for e in profile.experience if e.role]
    education = [
        " ".join(part for part in (e.degree, e.field, e.institution) if part)
        + (f", {e.graduation_year}" if e.graduation_year else "")
        for e in profile.education
    ]
    return (
        f"Name: {profile.personal.name or 'the sender'}\n"
        f"Location: {profile.personal.location or 'unknown'}\n"
        f"Skills: {', '.join(skills) or 'unknown'}\n"
        f"Experience: {'; '.join(roles) or 'none listed'}\n"
        f"Education: {'; '.join(education) or 'none listed'}"
    )


def _build_prompt(contact: dict, profile: Profile, job: dict | None, spec: dict) -> str:
    reasons = ", ".join(contact.get("warmth_reasons") or []) or "none identified"
    job_block = (
        f"Title: {job.get('title')}\nCompany: {job.get('company')}\n"
        f"Details: {(job.get('description') or '')[:600]}"
        if job else "No specific role yet — they are interested in the company."
    )
    return (
        f"SENDER:\n{_sender_summary(profile)}\n\n"
        f"RECIPIENT:\n"
        f"Name: {contact.get('name')}\n"
        f"Role: {contact.get('current_role') or 'unknown'}\n"
        f"Company: {contact.get('current_company')}\n"
        f"Relationship: {contact.get('degree_type') or '2nd'}-degree\n"
        f"Why this person was picked: {reasons}\n\n"
        f"ROLE BEING DISCUSSED:\n{job_block}\n\n"
        f"TASK: {spec['intent']}.\n"
        f"Keep the message under {spec['max_words']} words."
    )


def draft_message(contact: dict, profile: Profile, job: dict | None = None,
                  message_type: str | None = None) -> OutreachDraft:
    """Draft one message for review. Retries because model output is not
    deterministic; raises rather than handing the user something broken."""
    message_type = message_type or pick_message_type(contact)
    spec = MESSAGE_TYPES.get(message_type) or MESSAGE_TYPES["cold_intro"]
    prompt = _build_prompt(contact, profile, job, spec)

    last_error: Exception | None = None
    for _ in range(_MAX_ATTEMPTS):
        try:
            raw = complete(prompt, system=SYSTEM_PROMPT, max_tokens=_DRAFT_MAX_TOKENS)
            data = json.loads(_strip_fences(raw))
            draft = OutreachDraft.model_validate({
                **data,
                "message_type": message_type,
                "channel": spec["channel"],
            })
            # A DM has no subject line however the model formats its reply.
            if spec["channel"] != "email":
                draft.subject = None
            return draft
        except Exception as exc:
            last_error = exc

    raise ValueError(
        f"could not draft a {message_type} for {contact.get('name')!r} "
        f"after {_MAX_ATTEMPTS} attempts: {last_error}"
    )
