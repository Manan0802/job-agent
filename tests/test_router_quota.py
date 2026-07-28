"""Not wasting the primary's daily allowance.

A real run showed Gemini's free tier is 20 requests *per day* for
gemini-3.5-flash. Retrying that is not just useless — each retry spends one of
the twenty, so the retry policy written for transient 503s actively made the
outage worse.
"""

import pytest
from unittest.mock import MagicMock, patch

from backend.llm import router

_DAILY_QUOTA_429 = (
    "Error code: 429 - {'error': {'code': 429, 'message': 'You exceeded your current "
    "quota... Quota exceeded for metric: generativelanguage.googleapis.com/"
    "generate_content_free_tier_requests, limit: 20', 'status': 'RESOURCE_EXHAUSTED', "
    "'details': [{'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier'}]}}"
)
_TRANSIENT_503 = "Error code: 503 - model is overloaded, please try again"


def _answering(text):
    resp = MagicMock()
    resp.choices[0].message.content = text
    return resp


@pytest.fixture(autouse=True)
def _no_sleeping(monkeypatch):
    monkeypatch.setattr(router.time, "sleep", lambda _: None)


def test_a_daily_quota_error_is_not_retried(monkeypatch):
    """Each retry spends one of the twenty it just said were gone."""
    primary = MagicMock(side_effect=Exception(_DAILY_QUOTA_429))
    monkeypatch.setattr(router._client.chat.completions, "create", primary)
    monkeypatch.setattr(
        router._groq_client.chat.completions, "create",
        MagicMock(return_value=_answering("from fallback")),
    )

    assert router.complete("hi") == "from fallback"
    assert primary.call_count == 1


def test_a_transient_error_still_gets_its_retries(monkeypatch):
    """Load-shedding does clear on its own, which is why retrying exists."""
    primary = MagicMock(side_effect=[
        Exception(_TRANSIENT_503), Exception(_TRANSIENT_503), _answering("recovered"),
    ])
    monkeypatch.setattr(router._client.chat.completions, "create", primary)

    assert router.complete("hi") == "recovered"
    assert primary.call_count == 3


def test_a_spent_daily_quota_stays_shut_for_longer_than_a_blip(monkeypatch):
    """A daily cap will not clear in two minutes, so re-probing every two
    minutes just burns the next day's allowance early."""
    monkeypatch.setattr(
        router._client.chat.completions, "create",
        MagicMock(side_effect=Exception(_DAILY_QUOTA_429)),
    )
    monkeypatch.setattr(
        router._groq_client.chat.completions, "create",
        MagicMock(return_value=_answering("x")),
    )

    router.complete("hi", model="cheap")

    shut_for = router._primary_down_until["cheap"] - router.time.time()
    assert shut_for > router._PRIMARY_COOLDOWN_SECONDS


def test_the_sdk_does_not_retry_underneath_us():
    """The client's own retries multiply ours: three attempts became nine
    requests against a twenty-a-day budget."""
    assert router._client.max_retries == 0
    assert router._groq_client.max_retries == 0
