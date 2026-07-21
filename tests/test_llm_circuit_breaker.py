"""When Gemini is shedding load it stays down for minutes, so re-running its
full retry budget on every single job wastes ~18s each time. After a full
failure the primary is skipped briefly and traffic goes straight to Groq.
"""

from unittest.mock import patch, MagicMock
from backend.llm import router


def _ok(text: str = "ok"):
    fake = MagicMock()
    fake.choices = [MagicMock(message=MagicMock(content=text))]
    return fake


def test_second_call_skips_the_dead_primary_entirely():
    with patch.object(router, "_client") as primary, \
         patch.object(router, "_groq_client") as groq, \
         patch.object(router.time, "sleep"):
        primary.chat.completions.create.side_effect = Exception("503")
        groq.chat.completions.create.return_value = _ok("from groq")

        router.complete("first")
        calls_after_first = primary.chat.completions.create.call_count
        router.complete("second")

        assert calls_after_first == router._PRIMARY_ATTEMPTS
        assert primary.chat.completions.create.call_count == calls_after_first
        assert groq.chat.completions.create.call_count == 2


def test_primary_is_retried_again_once_the_cooldown_expires():
    with patch.object(router, "_client") as primary, \
         patch.object(router, "_groq_client") as groq, \
         patch.object(router.time, "sleep"):
        primary.chat.completions.create.side_effect = Exception("503")
        groq.chat.completions.create.return_value = _ok()
        router.complete("first")

        # jump past the cooldown
        router._primary_down_until = router.time.time() - 1
        primary.chat.completions.create.side_effect = None
        primary.chat.completions.create.return_value = _ok("recovered")
        assert router.complete("second") == "recovered"


def test_a_healthy_primary_never_trips_the_breaker():
    with patch.object(router, "_client") as primary, patch.object(router, "_groq_client") as groq:
        primary.chat.completions.create.return_value = _ok("fine")
        router.complete("one")
        router.complete("two")
    assert primary.chat.completions.create.call_count == 2
    groq.chat.completions.create.assert_not_called()


def test_primary_recovering_mid_run_clears_the_breaker():
    with patch.object(router, "_client") as primary, \
         patch.object(router, "_groq_client") as groq, \
         patch.object(router.time, "sleep"):
        primary.chat.completions.create.side_effect = [Exception("503"), _ok("recovered")]
        groq.chat.completions.create.return_value = _ok("from groq")
        assert router.complete("one") == "recovered"

    assert router._primary_down_until == 0.0
    groq.chat.completions.create.assert_not_called()
