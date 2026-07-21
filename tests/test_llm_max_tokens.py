"""Regression test: an unset max_tokens truncated real Groq output mid-JSON."""

from unittest.mock import patch, MagicMock
from backend.llm import router


def _fake_response(text: str = "ok"):
    fake = MagicMock()
    fake.choices = [MagicMock(message=MagicMock(content=text))]
    return fake


def test_complete_requests_enough_output_tokens():
    with patch.object(router, "_client") as client:
        client.chat.completions.create.return_value = _fake_response()
        router.complete("parse this resume")
    _, kwargs = client.chat.completions.create.call_args
    assert kwargs["max_tokens"] >= 4000


def test_groq_fallback_also_requests_enough_output_tokens():
    with patch.object(router, "_client") as primary, \
         patch.object(router, "_groq_client") as groq, \
         patch.object(router.time, "sleep"):
        primary.chat.completions.create.side_effect = Exception("gemini 503")
        groq.chat.completions.create.return_value = _fake_response()
        router.complete("parse this resume")
    _, kwargs = groq.chat.completions.create.call_args
    assert kwargs["max_tokens"] >= 4000
