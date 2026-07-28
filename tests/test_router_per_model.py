"""One exhausted model must not disable the others.

Gemini's free quota is per model per day — the refusal names
`GenerateRequestsPerDayPerProjectPerModel`. A single breaker for "the primary"
therefore threw away allowance that was still there: the cheap model running
out of its budget also stopped the heavier one from being tried.
"""

import pytest
from unittest.mock import MagicMock

from backend.llm import router

_DAILY_QUOTA_429 = (
    "Error code: 429 - Quota exceeded, limit: 20, "
    "quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier"
)


def _answering(text):
    resp = MagicMock()
    resp.choices[0].message.content = text
    return resp


@pytest.fixture(autouse=True)
def _no_sleeping(monkeypatch):
    monkeypatch.setattr(router.time, "sleep", lambda _: None)


def test_exhausting_one_model_leaves_another_usable(monkeypatch):
    def create(model, **_):
        if model == "cheap":
            raise Exception(_DAILY_QUOTA_429)
        return _answering("from heavy")

    monkeypatch.setattr(router._client.chat.completions, "create", MagicMock(side_effect=create))
    monkeypatch.setattr(
        router._groq_client.chat.completions, "create",
        MagicMock(return_value=_answering("from fallback")),
    )

    assert router.complete("hi", model="cheap") == "from fallback"
    assert router.complete("hi", model="heavy") == "from heavy"


def test_availability_is_asked_per_model(monkeypatch):
    monkeypatch.setattr(
        router._client.chat.completions, "create",
        MagicMock(side_effect=Exception(_DAILY_QUOTA_429)),
    )
    monkeypatch.setattr(
        router._groq_client.chat.completions, "create",
        MagicMock(return_value=_answering("x")),
    )

    router.complete("hi", model="cheap")

    assert router.primary_is_available("cheap") is False
    assert router.primary_is_available("heavy") is True


def test_asking_without_naming_one_means_the_configured_model(monkeypatch):
    """job_scorer asks this to decide how wide to fan out, and it does not pass
    a model, so the answer has to be about the model it will actually use."""
    monkeypatch.setattr(
        router._client.chat.completions, "create",
        MagicMock(side_effect=Exception(_DAILY_QUOTA_429)),
    )
    monkeypatch.setattr(
        router._groq_client.chat.completions, "create",
        MagicMock(return_value=_answering("x")),
    )

    router.complete("hi")

    assert router.primary_is_available() is False


def test_resetting_clears_every_model(monkeypatch):
    monkeypatch.setattr(
        router._client.chat.completions, "create",
        MagicMock(side_effect=Exception(_DAILY_QUOTA_429)),
    )
    monkeypatch.setattr(
        router._groq_client.chat.completions, "create",
        MagicMock(return_value=_answering("x")),
    )
    router.complete("hi", model="a")
    router.complete("hi", model="b")

    router.reset_primary_breaker()

    assert router.primary_is_available("a") and router.primary_is_available("b")
