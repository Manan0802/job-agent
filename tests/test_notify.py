import json
from unittest.mock import patch, MagicMock

from backend.services import notify


def _ok_response():
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    return resp


def test_sends_message_to_configured_chat():
    with patch.object(notify, "_settings") as s, patch.object(notify.httpx, "post") as post:
        s.telegram_bot_token = "tok123"
        s.telegram_chat_id = "chat456"
        post.return_value = _ok_response()
        assert notify.send_telegram_alert("23 new jobs") is True

    url = post.call_args[0][0]
    assert "tok123" in url and url.endswith("/sendMessage")
    assert post.call_args.kwargs["json"]["chat_id"] == "chat456"
    assert post.call_args.kwargs["json"]["text"] == "23 new jobs"


def test_skips_silently_when_not_configured():
    """An unconfigured notifier must not break a job hunt that otherwise worked."""
    with patch.object(notify, "_settings") as s, patch.object(notify.httpx, "post") as post:
        s.telegram_bot_token = ""
        s.telegram_chat_id = ""
        assert notify.send_telegram_alert("hello") is False
    post.assert_not_called()


def test_telegram_outage_does_not_raise():
    with patch.object(notify, "_settings") as s, patch.object(notify.httpx, "post") as post:
        s.telegram_bot_token = "tok"
        s.telegram_chat_id = "chat"
        post.side_effect = RuntimeError("telegram is down")
        assert notify.send_telegram_alert("hello") is False


def test_alert_leads_with_the_count_and_lists_top_matches():
    jobs = [
        {"title": "AI Engineer", "company": "Zepto", "url": "https://x.com/1", "llm_score": 87.0},
        {"title": "ML Engineer", "company": "Swiggy", "url": "https://x.com/2", "llm_score": 72.0},
    ]
    text = notify.format_job_alert(jobs, total_found=355)

    assert "355" in text
    assert "AI Engineer" in text and "Zepto" in text
    assert "87" in text
    assert "https://x.com/1" in text


def test_alert_caps_how_many_jobs_it_lists():
    jobs = [
        {"title": f"Job {i}", "company": "X", "url": f"https://x.com/{i}", "llm_score": 90.0 - i}
        for i in range(20)
    ]
    text = notify.format_job_alert(jobs, total_found=20)
    assert "Job 0" in text
    assert "Job 19" not in text


def test_alert_handles_an_empty_run():
    text = notify.format_job_alert([], total_found=0)
    assert text
    assert "0" in text or "no" in text.lower()


def test_alert_survives_a_job_that_failed_scoring():
    jobs = [{"title": "AI Engineer", "company": "Zepto", "url": "u", "llm_score": None}]
    assert "AI Engineer" in notify.format_job_alert(jobs, total_found=1)
