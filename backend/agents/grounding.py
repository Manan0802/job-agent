"""Turning a profile and a posting into prompt text, and checking what came back.

Both resume tailoring and interview prep need the same three things: the
resume rendered as text, the posting rendered as text, and a check on whether
the model's answer leans on experience the resume never mentions.

That last one exists because prompting alone did not stop it. A live run
produced "Experienced in building distributed, scalable backend systems" for
a resume that never says distributed.
"""

import re

from backend.schemas.profile import Profile

_DESCRIPTION_CHARS = 2500


def strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def resume_text(profile: Profile) -> str:
    s = profile.skills
    skills = [*s.languages, *s.frameworks, *s.ai_ml, *s.tools, *s.databases]

    experience = []
    for e in profile.experience:
        line = f"- {e.role or 'role'} at {e.company or 'company'}"
        if e.highlights:
            line += "\n" + "\n".join(f"    · {h}" for h in e.highlights)
        if e.tech_used:
            line += f"\n    (tech: {', '.join(e.tech_used)})"
        experience.append(line)

    education = [
        " ".join(part for part in (e.degree, e.field, e.institution) if part)
        for e in profile.education
    ]

    return (
        f"Name: {profile.personal.name or 'the candidate'}\n"
        f"Skills listed: {', '.join(skills) or 'none'}\n"
        f"Experience:\n{chr(10).join(experience) or '  none listed'}\n"
        f"Education: {'; '.join(e for e in education if e) or 'none listed'}\n"
        f"Keywords: {', '.join(profile.keywords) or 'none'}"
    )


def job_meta(job: dict) -> str:
    """The company and title, which any letter is expected to name."""
    return f"{job.get('company') or ''} {job.get('title') or ''}"


def job_text(job: dict) -> str:
    return (
        f"Title: {job.get('title')}\n"
        f"Company: {job.get('company')}\n"
        f"Posting: {(job.get('description') or '')[:_DESCRIPTION_CHARS]}"
    )


# Words too generic to be a claim about capability.
_HARMLESS = {
    "and", "the", "for", "with", "your", "you", "add", "lead", "move", "top",
    "list", "line", "bullet", "section", "summary", "skills", "experience",
    "resume", "role", "job", "posting", "this", "that", "from", "into", "which",
    "using", "used", "use", "work", "working", "team", "teams", "new", "more",
    "make", "makes", "show", "shows", "put", "start", "first", "rewrite",
    "rephrase", "highlight", "mention", "emphasise", "emphasize", "including",
    # Auxiliaries and connectives that carry no claim, but do turn up in
    # postings ("nice to have", "experience across ...").
    "have", "has", "had", "been", "were", "will", "can", "could", "should",
    "would", "across", "under", "over", "also", "both", "each", "other",
    "than", "then", "there", "these", "those", "them", "their", "when",
    "where", "while", "such", "very", "most", "many", "some", "any", "all",
    "ensure", "ensuring", "describing", "describe", "include", "note", "line",
    "sentence", "brief", "place", "reorder", "under", "top",
    # Generic verbs: the claim lives in what follows them, not in the verb.
    "build", "building", "built", "create", "creating", "created", "deliver",
}


# Ways of saying "you do not have this". A term named inside one of these is
# being admitted to, not claimed.
_ADMISSION = re.compile(
    r"\b(lacks?|lacking|missing|absent|gap|no experience|not shown|does not show|"
    r"doesn't show|do not have|don't have|have not|haven't|has not|hasn't|"
    r"never used|without)\b",
    re.IGNORECASE,
)
# Clause boundaries. "Acknowledge the lack of Java, but emphasise Kubernetes"
# admits one thing and claims another, so the admission must not cover both.
_CLAUSE = re.compile(r"(?:[.;:!?]\s+)|(?:,?\s+(?:but|although|though|however|while)\s+)")


def unsupported_terms(
    text: str, resume: str, job: str, job_meta: str = "", named_only: bool = False
) -> list[str]:
    """Words the text took from the posting that the resume never backs.

    A live run produced "Experienced in building distributed, scalable backend
    systems" for a resume that never says distributed. The instruction not to
    invent was already in the prompt and did not hold, so this checks.

    Two things are deliberately not flagged, because a warning that is usually
    wrong teaches the user to click past it:

    - `job_meta` (the company and title) — naming the employer you are writing
      to is expected.
    - anything named inside an admission of not having it. A live run produced
      "Acknowledge the lack of Java on the resume" and this read it as a boast,
      when the advice was exactly right. The check runs per clause, so a claim
      that follows an admission is still caught.

    `named_only` narrows it to capitalised technology names. Tailoring wants
    the wide rule — its suggestions are terse edits, so a lowercase claim like
    "distributed" is the whole point. Interview prep is prose about the role,
    where the wide rule flagged "about", "high" and "designing" across five of
    six answers, none of them real. What can actually be falsely rehearsed
    there is a named technology.
    """
    resume_words = set(re.findall(r"[a-z]+", resume.lower()))
    job_words = set(re.findall(r"[a-z]+", job.lower()))
    meta_words = set(re.findall(r"[a-z]+", job_meta.lower()))

    flagged: list[str] = []
    for clause in _CLAUSE.split(text):
        if _ADMISSION.search(clause):
            continue
        # Skip the first word: a sentence-initial capital says nothing.
        words = re.findall(r"[A-Za-z][A-Za-z+#.-]{3,}", clause)
        for position, word in enumerate(words):
            if named_only and not (word[0].isupper() and position > 0):
                continue
            clean = word.lower().strip(".-")
            if clean in _HARMLESS or clean in resume_words or clean in meta_words:
                continue
            if clean not in job_words or clean in flagged:
                continue
            flagged.append(clean)
    return flagged
