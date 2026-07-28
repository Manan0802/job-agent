"""LLM job scoring — the one expensive step, so it only ever sees the shortlist.

The embedding pre-filter narrows hundreds of scraped jobs down to a handful
before anything reaches here.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor

from backend.llm.errors import ModelUnavailable
from backend.llm.router import complete, primary_is_available
from backend.schemas.job_score import JobScore
from backend.schemas.profile import Profile

log = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
_DESCRIPTION_CHARS = 2000
# Wide enough to matter, narrow enough that a shortlist does not burst past
# the free tier's per-minute request limit.
_MAX_CONCURRENT = 5
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
    raise ModelUnavailable(
        f"could not score job {job.get('title')!r} after {_MAX_ATTEMPTS} attempts: {last_error}"
    )


def _score_one(job: dict, profile: Profile) -> dict:
    try:
        result = score_job(job, profile)
        return {**job, "llm_score": result.score, "llm_breakdown": result.model_dump_json()}
    except Exception as exc:
        log.warning("scoring failed for %r: %s", job.get("title"), exc)
        return {**job, "llm_score": None, "llm_breakdown": None}


def score_jobs(jobs: list[dict], profile: Profile) -> list[dict]:
    """Score every shortlisted job, best first.

    How wide this goes depends on which provider is answering: the primary
    allows far more per minute than the fallback, and pushing the fallback
    hard makes a run slower rather than faster.

    A job that can't be scored keeps its place with a null score rather than
    discarding the work already spent on the rest of the run.
    """
    if not jobs:
        return []

    # Score one on its own first. A fresh circuit breaker reports the primary
    # as healthy, so deciding up front would fan out five wide and only then
    # discover everything was falling to the fallback.
    scored = [_score_one(jobs[0], profile)]
    rest = jobs[1:]

    if rest:
        # Measured: with the primary down, five at a time made a real run
        # slower (13.5s a job against 4.3s sequential). The fallback's ceiling
        # is tokens per minute, not requests, so parallelism there only buys
        # 429s and backoff.
        workers = min(_MAX_CONCURRENT if primary_is_available() else 1, len(rest))
        log.info("scoring %d more jobs, %d at a time", len(rest), workers)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            scored.extend(pool.map(lambda job: _score_one(job, profile), rest))

    scored.sort(key=lambda j: j["llm_score"] if j["llm_score"] is not None else -1, reverse=True)
    return scored
