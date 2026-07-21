"""Groq counts max_tokens toward its per-minute admission budget, so reserving
a resume-sized reply for every small job score throttles the run (8/10 calls
admitted at 6000 vs 10/10 at 1200).
"""

from unittest.mock import patch, MagicMock
from backend.llm import router
from backend.agents import job_scorer
from backend.schemas.profile import Profile


def _ok(text: str = "ok"):
    fake = MagicMock()
    fake.choices = [MagicMock(message=MagicMock(content=text))]
    return fake


def test_caller_can_request_a_smaller_reply():
    with patch.object(router, "_client") as primary:
        primary.chat.completions.create.return_value = _ok()
        router.complete("score this", max_tokens=1200)
    assert primary.chat.completions.create.call_args.kwargs["max_tokens"] == 1200


def test_fallback_honours_the_same_request():
    with patch.object(router, "_client") as primary, \
         patch.object(router, "_groq_client") as groq, \
         patch.object(router.time, "sleep"):
        primary.chat.completions.create.side_effect = Exception("503")
        groq.chat.completions.create.return_value = _ok()
        router.complete("score this", max_tokens=1200)
    assert groq.chat.completions.create.call_args.kwargs["max_tokens"] == 1200


def test_omitting_it_keeps_the_generous_default():
    with patch.object(router, "_client") as primary:
        primary.chat.completions.create.return_value = _ok()
        router.complete("parse this resume")
    assert primary.chat.completions.create.call_args.kwargs["max_tokens"] >= 4000


def test_scoring_asks_for_a_small_reply():
    """A job score is a few hundred tokens; asking for thousands throttles Groq."""
    with patch.object(job_scorer, "complete", return_value='{"score": 50}') as c:
        job_scorer.score_job({"title": "AI Engineer"}, Profile())
    assert 0 < c.call_args.kwargs["max_tokens"] <= 2000
