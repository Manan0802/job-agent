"""Free-first LLM routing: Gemini primary, Groq as the safety net.

Gemini sheds load with transient 503s. Falling back on the very first one
drained Groq's much smaller free budget (8k tokens/min) and left job scoring
crawling at ~41s per job, so the primary gets a few short retries first.
"""

import logging
import time

from openai import OpenAI

from backend.config import get_settings

log = logging.getLogger(__name__)

_settings = get_settings()
_client = OpenAI(api_key=_settings.llm_api_key or "missing", base_url=_settings.llm_base_url)
_groq_client = OpenAI(api_key=_settings.groq_api_key or "missing", base_url=_settings.groq_base_url)

_PRIMARY_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = 2.0
# Gemini's load-shedding lasts minutes, so once it has clearly gone down there
# is no point paying the full retry budget again on the very next job.
_PRIMARY_COOLDOWN_SECONDS = 120.0

_primary_down_until = 0.0


def reset_primary_breaker() -> None:
    global _primary_down_until
    _primary_down_until = 0.0


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
