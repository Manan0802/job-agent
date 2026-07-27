"""How likely is this person to actually refer you?

The PRD's warmth table is written around one candidate ("DTU alumni",
"Delhi-based"). Here the alma mater, home city, employers and tech stack all
come from the user's own profile, so the same scoring works for any user.
"""

import re

from backend.schemas.profile import Profile
from backend.utils.text import company_key, contains_word, institution_aliases

_SENIOR_TITLES = re.compile(
    r"\b(sde[\s\-]?[23]|sde[\s\-]?ii|sde[\s\-]?iii|senior|staff|principal|lead|"
    r"manager|head|director|architect|vp)\b",
    re.IGNORECASE,
)

_LOCATION_NOISE = {"india", "the", "of", "and"}


def _text_of(contact: dict) -> str:
    return " ".join(
        str(contact.get(field) or "")
        for field in ("education", "headline", "current_role", "location", "name")
    ).lower()


def _is_alumni(contact: dict, profile: Profile) -> str | None:
    haystack = _text_of(contact)
    for education in profile.education:
        if any(contains_word(haystack, alias)
               for alias in institution_aliases(education.institution)):
            return education.institution
    return None


def _shared_employer(contact: dict, profile: Profile) -> str | None:
    haystack = _text_of(contact)
    current = company_key(contact.get("current_company"))
    for experience in profile.experience:
        key = company_key(experience.company)
        if key and key != current and contains_word(haystack, key):
            return experience.company
    return None


def _shared_stack(contact: dict, profile: Profile) -> list[str]:
    haystack = _text_of(contact)
    skills = profile.skills
    everything = [*skills.languages, *skills.frameworks, *skills.ai_ml,
                  *skills.tools, *skills.databases]
    return [s for s in everything if s and contains_word(haystack, s)]


def _same_city(contact: dict, profile: Profile) -> bool:
    def places(value: str | None) -> set[str]:
        return {w for w in re.findall(r"[a-z]+", (value or "").lower())
                if w not in _LOCATION_NOISE}

    home = places(profile.personal.location)
    return bool(home) and bool(home & places(contact.get("location")))


def score_contact(contact: dict, profile: Profile) -> tuple[int, list[str]]:
    """Return a 1-5 warmth score and the reasons behind it.

    The reasons matter as much as the number: the user decides who to actually
    message, so they need to see why someone was ranked first.
    """
    is_connection = (contact.get("degree_type") or "").lower().startswith("1")
    alumni = _is_alumni(contact, profile)
    reasons: list[str] = []

    if alumni and is_connection:
        score = 5
        reasons += [f"{alumni} alumni", "already a 1st-degree connection"]
    elif alumni:
        score = 4
        reasons.append(f"{alumni} alumni")
    elif is_connection:
        score = 3
        reasons.append("already a 1st-degree connection")
    else:
        score = 1
        reasons.append(f"works at {contact.get('current_company') or 'the company'}")

    if not is_connection and not alumni:
        role = contact.get("current_role") or ""
        if _SENIOR_TITLES.search(role):
            score = max(score, 2)
            reasons.append(f"senior enough to refer ({role})")
        shared = _shared_stack(contact, profile)
        if shared:
            score = max(score, 2)
            reasons.append(f"shares your stack ({', '.join(shared[:3])})")

    employer = _shared_employer(contact, profile)
    if employer:
        score = min(score + 1, 5)
        reasons.append(f"also worked at {employer}")

    if _same_city(contact, profile):
        reasons.append("based in your city")

    return score, reasons
