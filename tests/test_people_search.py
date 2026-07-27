"""Finding potential referrers through public Google results.

LinkedIn de-indexed headlines and work history in 2024, so a SERP result now
reliably yields only name, profile URL and current employer (from the page
title). That is enough: the user clicks through to decide.
"""

from unittest.mock import MagicMock, patch

from backend.db.database import init_db
from backend.services import people_search
from backend.services.api_budget import record_call

SERPER = {
    "organic": [
        {"title": "Asha Rao - SDE-2 - Zepto | LinkedIn",
         "link": "https://in.linkedin.com/in/asha-rao",
         "snippet": "Ex-IndiaMART. Python, LangGraph."},
        {"title": "Zepto | LinkedIn",
         "link": "https://www.linkedin.com/company/zepto",
         "snippet": "Zepto official page"},
        {"title": "Ravi Kumar - Zepto | LinkedIn",
         "link": "https://www.linkedin.com/in/ravi-kumar",
         "snippet": "Engineering at Zepto"},
    ]
}

SERPAPI = {
    "organic_results": [
        {"title": "Priya Singh - Zepto | LinkedIn",
         "link": "https://www.linkedin.com/in/priya-singh",
         "snippet": "Building at Zepto"},
    ]
}


def _settings(monkeypatch, **overrides):
    fake = MagicMock()
    fake.serper_api_key = overrides.get("serper", "")
    fake.serpapi_api_key = overrides.get("serpapi", "")
    fake.serper_monthly_cap = overrides.get("serper_cap", 2500)
    fake.serpapi_monthly_cap = overrides.get("serpapi_cap", 250)
    monkeypatch.setattr(people_search, "_settings", fake)
    return fake


def _response(payload):
    resp = MagicMock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


def test_query_targets_public_linkedin_profiles(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "q.db"))
    init_db()
    _settings(monkeypatch, serper="k")

    with patch.object(people_search.httpx, "post", return_value=_response(SERPER)) as post:
        people_search.search_people("Zepto", role="engineer", location="India")

    query = post.call_args.kwargs["json"]["q"]
    assert "site:linkedin.com/in" in query
    assert "Zepto" in query and "engineer" in query and "India" in query


def test_parses_name_role_and_company_out_of_the_result_title(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "p.db"))
    init_db()
    _settings(monkeypatch, serper="k")

    with patch.object(people_search.httpx, "post", return_value=_response(SERPER)):
        people = people_search.search_people("Zepto")

    asha = people[0]
    assert asha["name"] == "Asha Rao"
    assert asha["current_role"] == "SDE-2"
    assert asha["current_company"] == "Zepto"
    assert asha["linkedin_url"] == "https://in.linkedin.com/in/asha-rao"
    assert asha["headline"] == "Ex-IndiaMART. Python, LangGraph."
    assert asha["degree_type"] == "2nd"      # strangers until the CSV says otherwise
    assert asha["source"] == "search"


def test_titles_without_a_role_still_yield_a_person(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "n.db"))
    init_db()
    _settings(monkeypatch, serper="k")

    with patch.object(people_search.httpx, "post", return_value=_response(SERPER)):
        ravi = people_search.search_people("Zepto")[1]

    assert ravi["name"] == "Ravi Kumar"
    assert ravi["current_company"] == "Zepto"
    assert ravi["current_role"] is None


def test_company_pages_and_posts_are_not_people(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "f.db"))
    init_db()
    _settings(monkeypatch, serper="k")

    with patch.object(people_search.httpx, "post", return_value=_response(SERPER)):
        people = people_search.search_people("Zepto")

    assert all("/in/" in p["linkedin_url"] for p in people)
    assert len(people) == 2


def test_searching_spends_exactly_one_call(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "s.db"))
    init_db()
    _settings(monkeypatch, serper="k")

    with patch.object(people_search.httpx, "post", return_value=_response(SERPER)):
        people_search.search_people("Zepto")

    from backend.services.api_budget import remaining
    assert remaining("serper", 2500) == 2499


def test_an_exhausted_provider_hands_over_to_the_next(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "x.db"))
    init_db()
    _settings(monkeypatch, serper="k", serpapi="k2", serper_cap=1)
    record_call("serper", cap=1)          # burn Serper's only credit

    with patch.object(people_search.httpx, "post") as post, \
         patch.object(people_search.httpx, "get", return_value=_response(SERPAPI)) as get:
        people = people_search.search_people("Zepto")

    post.assert_not_called()
    get.assert_called_once()
    assert people[0]["name"] == "Priya Singh"


def test_a_failing_provider_hands_over_to_the_next(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "e.db"))
    init_db()
    _settings(monkeypatch, serper="k", serpapi="k2")

    with patch.object(people_search.httpx, "post", side_effect=RuntimeError("serper down")), \
         patch.object(people_search.httpx, "get", return_value=_response(SERPAPI)):
        assert people_search.search_people("Zepto")[0]["name"] == "Priya Singh"


def test_with_no_keys_configured_search_returns_nothing_quietly(tmp_path, monkeypatch):
    """The referral hunt still runs off the CSV and the manual link."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "k.db"))
    init_db()
    _settings(monkeypatch)

    with patch.object(people_search.httpx, "post") as post:
        assert people_search.search_people("Zepto") == []
    post.assert_not_called()


def test_a_manual_search_link_is_always_available():
    """Zero cost, no key, works when every budget is gone."""
    url = people_search.manual_search_url("Zepto", role="SDE", school="DTU")
    assert url.startswith("https://www.linkedin.com/search/")
    assert "Zepto" in url and "SDE" in url and "DTU" in url
