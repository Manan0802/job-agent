from backend.config import get_settings


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test/model:free")
    get_settings.cache_clear()
    s = get_settings()
    assert s.llm_api_key == "test-key"
    assert s.llm_model == "test/model:free"
    assert s.llm_base_url.startswith("https://")
