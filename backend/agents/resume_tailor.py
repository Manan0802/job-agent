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
from backend.agents.grounding import (
    job_meta as _job_meta,
    job_text as _job_text,
    resume_text as _resume_text,
    strip_fences as _strip_fences,
    unsupported_terms as _unsupported_terms,
)
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
    # Same check the resume suggestions get. The letter goes straight to the
    # employer, so it earns it more, not less.
    unsupported: list[str] = []

    @property
    def has_unsupported(self) -> bool:
        return bool(self.unsupported)


def _ask(prompt: str, system: str, max_tokens: int, what: str) -> dict:
    last_error: Exception | None = None
    for _ in range(_MAX_ATTEMPTS):
        try:
            raw = complete(prompt, system=system, max_tokens=max_tokens)
            return json.loads(_strip_fences(raw))
        except Exception as exc:
            last_error = exc
    raise ModelUnavailable(f"could not {what} after {_MAX_ATTEMPTS} attempts: {last_error}")


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
    meta = _job_meta(job)
    for suggestion in analysis.suggestions:
        suggestion.unsupported = _unsupported_terms(suggestion.change, resume, posting, meta)
    return analysis


def draft_cover_letter(job: dict, profile: Profile) -> CoverLetter:
    resume = _resume_text(profile)
    posting = _job_text(job)
    prompt = (
        f"JOB:\n{posting}\n\n"
        f"THE CANDIDATE'S RESUME:\n{resume}\n\n"
        "Write the letter."
    )
    data = _ask(prompt, COVER_LETTER_PROMPT, _LETTER_MAX_TOKENS, "draft a cover letter")
    letter = CoverLetter.model_validate(data)
    letter.unsupported = _unsupported_terms(letter.body, resume, posting, _job_meta(job))
    return letter
