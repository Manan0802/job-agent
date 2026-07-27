"""Tailoring a resume to one job — honestly.

The failure mode this is built to avoid: a tool that "tailors" by adding
skills the user does not have. That gets found out in the interview and costs
them the role and the relationship.

So the analysis separates two things the model would otherwise conflate:
experience the user **has but buried** (worth rewriting to surface) from
experience they **genuinely lack** (worth knowing about, not worth faking).

This does not generate a resume file. The user's resume lives in whatever tool
they wrote it in, and a generated PDF would be a worse version of it. What
they need is which lines to change and why.
"""

import json
import logging

from pydantic import BaseModel

from backend.llm.errors import ModelUnavailable
from backend.llm.router import complete
from backend.schemas.profile import Profile
from backend.schemas.tailoring import FitAnalysis

log = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
# The fallback model spends roughly half its budget reasoning before it emits
# anything, so a smaller cap truncated the analysis mid-JSON.
_ANALYSIS_MAX_TOKENS = 3000
# Four sharp edits beat eight vague ones, and it keeps the reply inside budget.
_MAX_SUGGESTIONS = 4
_LETTER_MAX_TOKENS = 1500
_DESCRIPTION_CHARS = 2500

SYSTEM_PROMPT = (
    "You advise a candidate on tailoring their resume for one specific job. "
    "Return ONLY a valid JSON object — no preamble, no markdown fences.\n\n"
    "THE RULE THAT MATTERS MOST: never invent experience, skills, employers, "
    "titles or numbers. Every suggestion must rework something the resume "
    "already contains. If the candidate lacks something, say so plainly rather "
    "than finding a way to imply they have it.\n\n"
    "Sort what the job wants into two piles, and keep them separate:\n"
    "- buried: the candidate HAS this, but the resume does not surface it "
    "(it sits in a skills list, or is hidden at the end of a bullet). These "
    "are the wins — rewriting for them costs nothing and changes everything.\n"
    "- missing: the candidate genuinely does NOT have this. Name it. Do not "
    "suggest wording that papers over it.\n\n"
    "Suggestions must be concrete enough to act on — which section, what to "
    "change, and what in the posting justifies it. Vague advice like "
    "'highlight relevant skills' is useless. Give at most four, and make them "
    "the four that matter. Keep each one to a sentence or two.\n\n"
    "Return exactly:\n"
    "{\n"
    '  "verdict": str, one honest sentence on the fit,\n'
    '  "strengths": [str], what already matches and should lead,\n'
    '  "buried": [str], what they have but did not surface,\n'
    '  "missing": [str], what they genuinely lack,\n'
    '  "suggestions": [{"section": str, "change": str, "why": str}]\n'
    "}"
)

COVER_LETTER_PROMPT = (
    "You write a short cover letter for a specific job. Return ONLY valid JSON.\n\n"
    "Never invent experience, employers, titles or numbers — use only what the "
    "resume below states. Open on the single most relevant thing the candidate "
    "has actually done, not on how excited they are. No flattery of the "
    "company. Keep it under 200 words; a page of prose does not get read.\n\n"
    "Return exactly:\n"
    "{\n"
    '  "body": str, the letter,\n'
    '  "opening_hook": str, the one thing you chose to open on\n'
    "}"
)


class CoverLetter(BaseModel):
    body: str
    opening_hook: str = ""


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def _resume_text(profile: Profile) -> str:
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


def _job_text(job: dict) -> str:
    return (
        f"Title: {job.get('title')}\n"
        f"Company: {job.get('company')}\n"
        f"Posting: {(job.get('description') or '')[:_DESCRIPTION_CHARS]}"
    )


def _ask(prompt: str, system: str, max_tokens: int, what: str) -> dict:
    last_error: Exception | None = None
    for _ in range(_MAX_ATTEMPTS):
        try:
            raw = complete(prompt, system=system, max_tokens=max_tokens)
            return json.loads(_strip_fences(raw))
        except Exception as exc:
            last_error = exc
    raise ModelUnavailable(f"could not {what} after {_MAX_ATTEMPTS} attempts: {last_error}")


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


def _unsupported_terms(text: str, resume: str, job: str) -> list[str]:
    """Words a suggestion took from the posting that the resume never backs.

    A live run produced "Experienced in building distributed, scalable backend
    systems" for a resume that never says distributed. The instruction not to
    invent was already in the prompt and did not hold, so this checks.
    """
    import re

    resume_words = set(re.findall(r"[a-z]+", resume.lower()))
    job_words = set(re.findall(r"[a-z]+", job.lower()))

    flagged = []
    for word in re.findall(r"[A-Za-z][A-Za-z+#.-]{3,}", text):
        clean = word.lower().strip(".-")
        if clean in _HARMLESS or clean in resume_words or clean not in job_words:
            continue
        if clean not in flagged:
            flagged.append(clean)
    return flagged


def analyze_fit(job: dict, profile: Profile) -> FitAnalysis:
    resume = _resume_text(profile)
    posting = _job_text(job)
    prompt = (
        f"JOB:\n{posting}\n\n"
        f"THE CANDIDATE'S RESUME AS IT STANDS:\n{resume}\n\n"
        "Work out what this posting asks for, then sort it into what the resume "
        "already proves, what it has but buries, and what it genuinely lacks."
    )
    data = _ask(prompt, SYSTEM_PROMPT, _ANALYSIS_MAX_TOKENS, "analyse this job")
    analysis = FitAnalysis.model_validate(data)

    analysis.suggestions = analysis.suggestions[:_MAX_SUGGESTIONS]
    for suggestion in analysis.suggestions:
        suggestion.unsupported = _unsupported_terms(suggestion.change, resume, posting)
    return analysis


def draft_cover_letter(job: dict, profile: Profile) -> CoverLetter:
    prompt = (
        f"JOB:\n{_job_text(job)}\n\n"
        f"THE CANDIDATE'S RESUME:\n{_resume_text(profile)}\n\n"
        "Write the letter."
    )
    data = _ask(prompt, COVER_LETTER_PROMPT, _LETTER_MAX_TOKENS, "draft a cover letter")
    return CoverLetter.model_validate(data)
