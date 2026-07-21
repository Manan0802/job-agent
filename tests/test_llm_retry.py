"""Gemini returns transient 503s. Dropping to Groq on the first one drained
Groq's 8k tokens/min free budget and made scoring ~41s per job.
"""

from unittest.mock import patch, MagicMock
from backend.llm import router


def _ok(text: str = "ok"):
    fake = MagicMock()
    fake.choices = [MagicMock(message=MagicMock(content=text))]
    return fake


def test_primary_is_retried_before_falling_back():
    with patch.object(router, "_client") as primary, \
         patch.object(router, "_groq_client") as groq, \
         patch.object(router.time, "sleep"):
        primary.chat.completions.create.side_effect = [Exception("503"), _ok("from gemini")]
        out = router.complete("hi")

    assert out == "from gemini"
    assert primary.chat.completions.create.call_count == 2
    groq.chat.completions.create.assert_not_called()


def test_falls_back_only_after_primary_exhausts_its_retries():
    with patch.object(router, "_client") as primary, \
         patch.object(router, "_groq_client") as groq, \
         patch.object(router.time, "sleep"):
        primary.chat.completions.create.side_effect = Exception("503")
        groq.chat.completions.create.return_value = _ok("from groq")
        out = router.complete("hi")

    assert out == "from groq"
    assert primary.chat.completions.create.call_count == router._PRIMARY_ATTEMPTS
    groq.chat.completions.create.assert_called_once()


def test_healthy_primary_is_called_exactly_once():
    with patch.object(router, "_client") as primary, patch.object(router, "_groq_client") as groq:
        primary.chat.completions.create.return_value = _ok("first try")
        out = router.complete("hi")

    assert out == "first try"
    assert primary.chat.completions.create.call_count == 1
    groq.chat.completions.create.assert_not_called()


def test_retries_wait_between_attempts():
    """Hammering a model that is shedding load just wastes the retry."""
    with patch.object(router, "_client") as primary, \
         patch.object(router, "_groq_client") as groq, \
         patch.object(router.time, "sleep") as sleep:
        primary.chat.completions.create.side_effect = Exception("503")
        groq.chat.completions.create.return_value = _ok()
        router.complete("hi")

    assert sleep.call_count >= 1
    assert all(call.args[0] > 0 for call in sleep.call_args_list)
