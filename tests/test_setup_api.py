"""What's configured and what each missing piece would unlock.

The security rule this pins down: the endpoint reports whether a key is set,
never the key itself.
"""

import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.api.routes import setup as setup_route
from backend.db.database import init_db
from backend.main import app

client = TestClient(app)

SECRET = "sk-super-secret-value-1234567890"


def _settings(**overrides):
    fake = MagicMock()
    fake.llm_api_key = overrides.get("llm", SECRET)
    fake.llm_model = "gemini-3.5-flash"
    fake.groq_api_key = overrides.get("groq", "")
    fake.groq_model = "openai/gpt-oss-20b"
    fake.serper_api_key = overrides.get("serper", "")
    fake.serpapi_api_key = overrides.get("serpapi", "")
    fake.serper_monthly_cap = 2500
    fake.serpapi_monthly_cap = 250
    fake.telegram_bot_token = overrides.get("telegram", "")
    fake.telegram_chat_id = overrides.get("chat", "")
    fake.linkedin_connections_csv = overrides.get("csv", "/nope/Connections.csv")
    fake.embedding_model = "BAAI/bge-small-en-v1.5"
    return fake


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "s.db"))
    init_db()


def _get(monkeypatch, **overrides):
    monkeypatch.setattr(setup_route, "_settings", _settings(**overrides))
    return client.get("/api/v1/setup").json()


def test_no_key_or_secret_is_ever_returned(db, monkeypatch):
    """Whatever else changes here, the response must stay safe to screenshot."""
    body = _get(monkeypatch, groq=SECRET, serper=SECRET, telegram=SECRET)

    assert SECRET not in str(body)
    assert "secret" not in str(body).lower()


def test_reports_which_pieces_are_configured(db, monkeypatch):
    body = _get(monkeypatch, serper="k")
    by_id = {item["id"]: item for item in body["items"]}

    assert by_id["llm"]["configured"] is True
    assert by_id["people_search"]["configured"] is True
    assert by_id["alerts"]["configured"] is False


def test_every_missing_piece_says_what_it_unlocks_and_where_to_get_it(db, monkeypatch):
    for item in _get(monkeypatch)["items"]:
        assert item["label"]
        assert item["unlocks"]
        if not item["configured"]:
            assert item["how"], item["id"]


def test_the_llm_is_the_only_required_piece(db, monkeypatch):
    required = [i["id"] for i in _get(monkeypatch)["items"] if i["required"]]
    assert required == ["llm"]


def test_a_missing_llm_key_is_called_out_as_blocking(db, monkeypatch):
    body = _get(monkeypatch, llm="")
    llm = next(i for i in body["items"] if i["id"] == "llm")

    assert llm["configured"] is False
    assert body["ready"] is False


def test_the_app_is_ready_once_the_llm_key_is_set(db, monkeypatch):
    assert _get(monkeypatch)["ready"] is True


def test_search_budget_is_reported_so_the_free_tier_is_visible(db, monkeypatch):
    from backend.services.api_budget import record_call

    record_call("serper", cap=2500)
    people = next(i for i in _get(monkeypatch, serper="k")["items"] if i["id"] == "people_search")

    assert people["detail"] and "2499" in people["detail"]


def test_a_provider_with_no_key_reports_no_budget_line(db, monkeypatch):
    people = next(i for i in _get(monkeypatch)["items"] if i["id"] == "people_search")
    assert not people["detail"]


def test_the_connections_export_is_detected_when_present(db, monkeypatch, tmp_path):
    csv = tmp_path / "Connections.csv"
    csv.write_text("First Name,Last Name,URL,Email Address,Company,Position,Connected On\n")

    body = _get(monkeypatch, csv=str(csv))
    assert next(i for i in body["items"] if i["id"] == "connections")["configured"] is True


def test_models_in_use_are_shown_so_a_stale_id_is_visible(db, monkeypatch):
    """Free model ids get retired; seeing which one is configured saves a lot
    of confused debugging."""
    llm = next(i for i in _get(monkeypatch)["items"] if i["id"] == "llm")
    assert "gemini-3.5-flash" in llm["detail"]
