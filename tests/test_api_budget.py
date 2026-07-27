"""Free search tiers are small (SerpApi resets at 250/month), so every metered
call is checked before it goes out.
"""

from backend.db.database import init_db
from backend.services.api_budget import can_spend, record_call, remaining


def test_a_fresh_provider_starts_with_its_whole_quota(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "a.db"))
    init_db()
    assert can_spend("serpapi", cap=250) is True
    assert remaining("serpapi", cap=250) == 250


def test_calls_count_against_the_quota(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "b.db"))
    init_db()
    for _ in range(3):
        record_call("serpapi", cap=250)
    assert remaining("serpapi", cap=250) == 247


def test_spending_stops_at_the_cap(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "c.db"))
    init_db()
    for _ in range(5):
        record_call("serpapi", cap=5)

    assert can_spend("serpapi", cap=5) is False
    assert remaining("serpapi", cap=5) == 0


def test_each_provider_has_its_own_quota(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "d.db"))
    init_db()
    record_call("serpapi", cap=250)
    assert remaining("serpapi", cap=250) == 249
    assert remaining("serper", cap=2500) == 2500


def test_a_new_month_restores_the_quota(tmp_path, monkeypatch):
    """SerpApi's free tier resets monthly, so last month's spend must not keep
    blocking calls."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "e.db"))
    init_db()
    record_call("serpapi", cap=2, month="2026-06")
    record_call("serpapi", cap=2, month="2026-06")
    assert can_spend("serpapi", cap=2, month="2026-06") is False
    assert can_spend("serpapi", cap=2, month="2026-07") is True


def test_a_zero_cap_blocks_everything(tmp_path, monkeypatch):
    """Setting a provider's cap to zero is how you turn it off."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "f.db"))
    init_db()
    assert can_spend("serpapi", cap=0) is False
