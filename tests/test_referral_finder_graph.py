"""The referral hunt: who at this company could get me in, warmest first.

Two sources feed it — the user's own LinkedIn export (1st-degree, free) and a
public Google search (2nd-degree, metered). Every external call is mocked here;
what is asserted is the flow.
"""

from unittest.mock import patch

import pytest

from backend.agents import referral_finder_graph as graph
from backend.db.database import init_db
from backend.schemas.profile import Education, Personal, Profile

PROFILE = Profile(
    personal=Personal(name="Manan", location="Delhi"),
    education=[Education(institution="Delhi Technological University (DTU)")],
)

CSV_CONTACT = {
    "name": "Asha Rao", "linkedin_url": "https://linkedin.com/in/asha-rao",
    "current_company": "Zepto", "current_role": "SDE-2", "email": "asha@x.com",
    "degree_type": "1st", "source": "csv",
}

SEARCH_STRANGER = {
    "name": "Ravi Kumar", "linkedin_url": "https://linkedin.com/in/ravi-kumar",
    "current_company": "Zepto", "current_role": "Engineering Manager",
    "headline": "DTU alum, engineering at Zepto", "degree_type": "2nd", "source": "search",
}

# The same person the CSV already knows, seen again in search results.
SEARCH_KNOWN = {
    "name": "Asha R.", "linkedin_url": "https://linkedin.com/in/asha-rao",
    "current_company": "Zepto", "current_role": "SDE-2",
    "headline": "Ex-IndiaMART", "degree_type": "2nd", "source": "search",
}


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "ref.db"))
    init_db()


def _run(csv_contacts, search_results, company="Zepto"):
    with patch.object(graph, "find_connections_at", return_value=csv_contacts), \
         patch.object(graph, "search_people", return_value=search_results):
        return graph.find_referrals(PROFILE, company)


def test_pulls_contacts_from_both_sources(db):
    result = _run([CSV_CONTACT], [SEARCH_STRANGER])

    assert result["company"] == "Zepto"
    assert {c["name"] for c in result["contacts"]} == {"Asha Rao", "Ravi Kumar"}


def test_someone_you_already_know_is_not_listed_twice(db):
    result = _run([CSV_CONTACT], [SEARCH_KNOWN, SEARCH_STRANGER])
    assert len(result["contacts"]) == 2


def test_knowing_someone_personally_outranks_what_the_search_says(db):
    """The search calls everyone a stranger; the user's own export knows better."""
    result = _run([CSV_CONTACT], [SEARCH_KNOWN])
    asha = result["contacts"][0]

    assert asha["degree_type"] == "1st"
    assert asha["email"] == "asha@x.com"          # kept from the CSV
    assert asha["headline"] == "Ex-IndiaMART"     # gained from the search


def test_contacts_come_back_warmest_first(db):
    contacts = _run([CSV_CONTACT], [SEARCH_STRANGER])["contacts"]
    scores = [c["warmth_score"] for c in contacts]

    assert len(contacts) == 2
    assert scores == sorted(scores, reverse=True)


def test_a_shared_college_beats_a_plain_linkedin_connection(db):
    """Per the PRD's warmth table: many 1st-degree connections are near
    strangers, while a fellow alum has a real reason to help."""
    contacts = {c["name"]: c["warmth_score"]
                for c in _run([CSV_CONTACT], [SEARCH_STRANGER])["contacts"]}

    assert contacts["Ravi Kumar"] > contacts["Asha Rao"]   # alum vs. plain connection


def test_every_contact_explains_its_own_ranking(db):
    for contact in _run([CSV_CONTACT], [SEARCH_STRANGER])["contacts"]:
        assert 1 <= contact["warmth_score"] <= 5
        assert contact["warmth_reasons"]


def test_the_hunt_is_saved_for_later(db):
    from backend.services.contact_store import load_contacts

    _run([CSV_CONTACT], [SEARCH_STRANGER])
    saved = load_contacts("Zepto")

    assert len(saved) == 2
    assert saved[0]["warmth_score"] >= saved[1]["warmth_score"]
    assert all(c["target_company"] == "Zepto" for c in saved)


def test_a_manual_search_link_is_always_offered(db):
    """Something to click even when both sources come back empty."""
    for csv_contacts, search_results in (([CSV_CONTACT], []), ([], []), ([], [SEARCH_STRANGER])):
        result = _run(csv_contacts, search_results)
        assert result["manual_search_url"].startswith("https://www.linkedin.com/search/")


def test_works_with_only_the_csv(db):
    """No search key configured — the free path still finds referrers."""
    result = _run([CSV_CONTACT], [])
    assert [c["name"] for c in result["contacts"]] == ["Asha Rao"]


def test_works_with_only_search(db):
    """No LinkedIn export yet."""
    result = _run([], [SEARCH_STRANGER])
    assert [c["name"] for c in result["contacts"]] == ["Ravi Kumar"]


def test_finding_nobody_is_a_clean_answer_not_an_error(db):
    result = _run([], [])
    assert result["contacts"] == []
    assert result["manual_search_url"]


def test_the_search_is_told_which_company_to_look_at(db):
    with patch.object(graph, "find_connections_at", return_value=[]), \
         patch.object(graph, "search_people", return_value=[]) as search:
        graph.find_referrals(PROFILE, "Swiggy", role="SDE")

    assert search.call_args[0][0] == "Swiggy"
    assert search.call_args.kwargs["role"] == "SDE"


def test_a_broken_source_does_not_sink_the_hunt(db):
    """A missing CSV or a dead search API still leaves the other source."""
    with patch.object(graph, "find_connections_at", side_effect=RuntimeError("no csv")), \
         patch.object(graph, "search_people", return_value=[SEARCH_STRANGER]):
        result = graph.find_referrals(PROFILE, "Zepto")

    assert [c["name"] for c in result["contacts"]] == ["Ravi Kumar"]
