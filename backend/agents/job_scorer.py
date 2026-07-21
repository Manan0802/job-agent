"""LLM job scoring — the one expensive step, so it only ever sees the shortlist.

The embedding pre-filter narrows hundreds of scraped jobs down to a handful
before anything reaches here.
"""

import json
import logging

from backend.llm.router import complete
from backend.schemas.job_score import JobScore
from backend.schemas.profile import Profile

log = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
_DESCRIPTION_CHARS = 2000
# A score reply runs a few hundred tokens; reserving more throttles Groq, which
# counts max_tokens against its per-minute admission budget.
_SCORE_MAX_TOKENS = 1200

SYSTEM_PROMPT = (
    "You judge how well a candidate fits a job. Return ONLY a valid JSON object, "
    "with no preamble, markdown fences, or explanation. Use exactly this structure:\n"
    "{\n"
    '  "score": number between 0 and 100,\n'
    '  "reasoning": str, one or two sentences,\n'
    '  "matched_skills": [str], skills the candidate already has for this role,\n'
    '  "missing_skills": [str], skills the job wants that the candidate lacks\n'
    "}\n"
    "Score honestly: 80+ means a strong fit worth applying to today, below 40 means "
    "a poor fit. Judge on real overlap, not enthusiasm."
)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def _candidate_summary(profile: Profile) -> str:
    s = profile.skills
    skills = [*s.languages, *s.frameworks, *s.ai_ml, *s.tools, *s.databases]
    roles = [f"{e.role} at {e.company}" for e in profile.experience if e.role]
    education = [f"{e.degree or ''} {e.field or ''}".strip() for e in profile.education]
    return (
        f"Skills: {', '.join(skills)}\n"
        f"Experience: {'; '.join(roles)}\n"
        f"Education: {'; '.join(e for e in education if e)}\n"
        f"Keywords: {', '.join(profile.keywords)}"
    )


def _build_prompt(job: dict, profile: Profile) -> str:
    return (
        "CANDIDATE:\n"
        f"{_candidate_summary(profile)}\n\n"
        "JOB:\n"
        f"Title: {job.get('title') or 'unknown'}\n"
        f"Company: {job.get('company') or 'unknown'}\n"
        f"Location: {job.get('location') or 'unknown'}\n"
        f"Description: {(job.get('description') or '')[:_DESCRIPTION_CHARS]}"
    )


def score_job(job: dict, profile: Profile) -> JobScore:
    """Score one job, retrying because model output is not deterministic."""
    prompt = _build_prompt(job, profile)
    last_error: Exception | None = None
    for _ in range(_MAX_ATTEMPTS):
        try:
            raw = complete(prompt, system=SYSTEM_PROMPT, max_tokens=_SCORE_MAX_TOKENS)
            return JobScore.model_validate(json.loads(_strip_fences(raw)))
        except Exception as exc:
            last_error = exc
    raise ValueError(
        f"could not score job {job.get('title')!r} after {_MAX_ATTEMPTS} attempts: {last_error}"
    )


def score_jobs(jobs: list[dict], profile: Profile) -> list[dict]:
    """Score every shortlisted job, best first.

    A job that can't be scored keeps its place with a null score rather than
    discarding the work already spent on the rest of the run.
    """
    scored: list[dict] = []
    for job in jobs:
        try:
            result = score_job(job, profile)
            scored.append({
                **job,
                "llm_score": result.score,
                "llm_breakdown": result.model_dump_json(),
            })
        except Exception as exc:
            log.warning("scoring failed for %r: %s", job.get("title"), exc)
            scored.append({**job, "llm_score": None, "llm_breakdown": None})
    scored.sort(key=lambda j: j["llm_score"] if j["llm_score"] is not None else -1, reverse=True)
    return scored
