from unittest.mock import patch, MagicMock
from backend.llm import router


def test_complete_returns_text():
    fake = MagicMock()
    fake.choices = [MagicMock(message=MagicMock(content="hello world"))]
    with patch.object(router, "_client") as client:
        client.chat.completions.create.return_value = fake
        out = router.complete("say hi", system="be brief")
    assert out == "hello world"
    _, kwargs = client.chat.completions.create.call_args
    assert kwargs["model"]  # non-empty
    assert kwargs["messages"][0]["role"] == "system"


def test_complete_falls_back_to_groq_on_error():
    fake = MagicMock()
    fake.choices = [MagicMock(message=MagicMock(content="from groq"))]
    with patch.object(router, "_client") as primary, \
         patch.object(router, "_groq_client") as fallback, \
         patch.object(router.time, "sleep"):
        primary.chat.completions.create.side_effect = Exception("rate limited")
        fallback.chat.completions.create.return_value = fake
        out = router.complete("say hi")
    assert out == "from groq"
    fallback.chat.completions.create.assert_called_once()
