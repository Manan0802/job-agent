"""Free-first LLM routing: Gemini primary, Groq as the safety net.

Gemini sheds load with transient 503s. Falling back on the very first one
drained Groq's much smaller free budget (8k tokens/min) and left job scoring
crawling at ~41s per job, so the primary gets a few short retries first.

Its free tier is also only 20 requests a day, so those retries are rationed:
a daily-quota refusal goes straight to the fallback, because retrying it spends
the very allowance it just said was gone.
"""

import logging
import time

from openai import OpenAI

from backend.config import get_settings

log = logging.getLogger(__name__)

_settings = get_settings()
# max_retries=0: the SDK retries 429s and 503s on its own, which multiplied
# with the retry loop below into nine requests per call against a 20-a-day
# budget. Retrying is this module's job, not the client's.
_client = OpenAI(
    api_key=_settings.llm_api_key or "missing",
    base_url=_settings.llm_base_url,
    max_retries=0,
)
_groq_client = OpenAI(
    api_key=_settings.groq_api_key or "missing",
    base_url=_settings.groq_base_url,
    max_retries=0,
)

_PRIMARY_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = 2.0
# Gemini's load-shedding lasts minutes, so once it has clearly gone down there
# is no point paying the full retry budget again on the very next job.
_PRIMARY_COOLDOWN_SECONDS = 120.0
# A daily cap will not clear in two minutes. Re-probing that often would spend
# tomorrow's allowance on finding out it is still today.
_DAILY_QUOTA_COOLDOWN_SECONDS = 1800.0

_primary_down_until = 0.0


def _is_daily_quota(exc: Exception) -> bool:
    """Whether the primary refused because the day's allowance is gone, rather
    than because it is momentarily busy. Both arrive as a 429."""
    text = str(exc)
    return "429" in text and ("PerDay" in text or "per day" in text)


def reset_primary_breaker() -> None:
    global _primary_down_until
    _primary_down_until = 0.0


def primary_is_available() -> bool:
    """Whether the primary is currently in play.

    Callers use this to decide how hard to push: the primary allows far more
    per minute than the fallback, so batching wide is only safe while it is up.
    """
    return time.time() >= _primary_down_until


def _try_primary(messages: list[dict], model: str | None, max_tokens: int) -> str | None:
    """Return the primary's answer, or None if it is unavailable right now."""
    global _primary_down_until
    if time.time() < _primary_down_until:
        return None

    for attempt in range(_PRIMARY_ATTEMPTS):
        try:
            resp = _client.chat.completions.create(
                model=model or _settings.llm_model,
                messages=messages,
                temperature=0.2,
                max_tokens=max_tokens,
            )
            _primary_down_until = 0.0
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            if _is_daily_quota(exc):
                _primary_down_until = time.time() + _DAILY_QUOTA_COOLDOWN_SECONDS
                log.warning(
                    "primary LLM out of daily quota; on the fallback for %.0fm",
                    _DAILY_QUOTA_COOLDOWN_SECONDS / 60,
                )
                return None
            log.info("primary LLM attempt %d/%d failed: %s", attempt + 1, _PRIMARY_ATTEMPTS, exc)
            if attempt < _PRIMARY_ATTEMPTS - 1:
                time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))

    _primary_down_until = time.time() + _PRIMARY_COOLDOWN_SECONDS
    log.warning("primary LLM down; routing to fallback for %.0fs", _PRIMARY_COOLDOWN_SECONDS)
    return None


def complete(
    prompt: str,
    system: str = "",
    model: str | None = None,
    max_tokens: int | None = None,
) -> str:
    """Ask for `max_tokens` no larger than the task needs: Groq counts it toward
    its per-minute admission budget, so an oversized reservation throttles runs.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    answer = _try_primary(messages, model, max_tokens or _settings.llm_max_tokens)
    if answer is not None:
        return answer

    resp = _groq_client.chat.completions.create(
        model=_settings.groq_model,
        messages=messages,
        temperature=0.2,
        max_tokens=max_tokens or _settings.groq_max_tokens,
    )
    return resp.choices[0].message.content.strip()
