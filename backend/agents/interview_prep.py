"""Preparing for one interview, without rehearsing things that never happened.

A generic list of interview questions is worth nothing — the internet is full
of them. What is worth something is knowing which questions *this* posting
makes likely, and which of your own experiences answers each one, so you
rehearse a real story instead of improvising.

The honesty check from resume tailoring is reused here and matters more. A
resume line you cannot back is embarrassing. A story you rehearsed and then
said out loud in an interview is worse, because you cannot walk it back.
"""

import json
import logging

from pydantic import BaseModel, Field

from backend.agents.grounding import (
    job_meta, job_text, resume_text, strip_fences, unsupported_terms,
)
from backend.llm.errors import ModelUnavailable
from backend.llm.router import complete
from backend.schemas.profile import Profile

log = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
_PREP_MAX_TOKENS = 3000
# More than this is not preparation, it is a reading list. Eight is what fits
# in the evening before an interview.
_MAX_QUESTIONS = 8

SYSTEM_PROMPT = (
    "You prepare a candidate for one specific interview. Return ONLY a valid "
    "JSON object — no preamble, no markdown fences.\n\n"
    "THE RULE THAT MATTERS MOST: every suggested answer must point at something "
    "the resume below actually contains. Never tell the candidate to describe "
    "work they have not done — they will say it out loud and cannot take it "
    "back. If the posting wants something they lack, put it in weak_spots "
    "instead, so they can prepare an honest answer.\n\n"
    "Questions must come from THIS posting, not from a generic list. Skip "
    "'tell me about yourself'. For each one, say what in the posting makes it "
    "likely and which of the candidate's own projects or results answers it.\n\n"
    "Return exactly:\n"
    "{\n"
    '  "role_focus": str, one sentence on what this interview is really testing,\n'
    '  "questions": [{"question": str, "why": str, "answer_from": str}],\n'
    '  "weak_spots": [str], what the posting wants that the resume does not '
    'show, phrased so they can prepare for being asked,\n'
    '  "ask_them": [str], questions worth asking the interviewer\n'
    "}"
)


def _ask(prompt: str, system: str) -> dict:
    last_error: Exception | None = None
    for _ in range(_MAX_ATTEMPTS):
        try:
            raw = complete(prompt, system=system, max_tokens=_PREP_MAX_TOKENS)
            return json.loads(strip_fences(raw))
        except Exception as exc:
            last_error = exc
    raise ModelUnavailable(
        f"could not prepare for this interview after {_MAX_ATTEMPTS} attempts: {last_error}"
    )


class Question(BaseModel):
    question: str
    why: str = ""           # what in the posting makes this likely
    answer_from: str = ""   # which of their own experiences answers it
    # Words the answer borrowed from the posting that the resume never backs.
    # Filled in by code, because prompting alone did not stop it in tailoring.
    unsupported: list[str] = Field(default_factory=list)


class InterviewPrep(BaseModel):
    role_focus: str = ""
    questions: list[Question] = Field(default_factory=list)
    weak_spots: list[str] = Field(default_factory=list)
    ask_them: list[str] = Field(default_factory=list)

    @property
    def has_unsupported(self) -> bool:
        """Whether any suggested answer would have them claim something new."""
        return any(q.unsupported for q in self.questions)


def prepare_for(job: dict, profile: Profile) -> InterviewPrep:
    resume = resume_text(profile)
    posting = job_text(job)
    prompt = (
        f"JOB:\n{posting}\n\n"
        f"THE CANDIDATE'S RESUME:\n{resume}\n\n"
        "Work out what this interview will actually probe, then write the "
        "questions they should expect and which of their own work answers each."
    )
    data = _ask(prompt, SYSTEM_PROMPT)
    prep = InterviewPrep.model_validate(data)

    prep.questions = prep.questions[:_MAX_QUESTIONS]
    meta = job_meta(job)
    for question in prep.questions:
        question.unsupported = unsupported_terms(question.answer_from, resume, posting, meta)
    return prep
