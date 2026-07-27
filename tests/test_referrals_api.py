from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api.routes import referrals as referrals_route
from backend.db.database import init_db
from backend.main import app
from backend.schemas.profile import Personal, Profile
from backend.services.contact_store import save_contacts

client = TestClient(app)

PROFILE = Profile(personal=Personal(name="Manan"))

FOUND = {
    "company": "Zepto",
    "contacts": [
        {"id": "a1", "name": "Asha Rao", "current_role": "SDE-2", "target_company": "Zepto",
         "linkedin_url": "https://linkedin.com/in/asha-rao", "degree_type": "1st",
         "warmth_score": 5, "warmth_reasons": '["DTU alumni", "1st-degree connection"]',
         "source": "csv", "outreach_status": "pending"},
    ],
    "manual_search_url": "https://www.linkedin.com/search/results/people/?keywords=Zepto",
}


def test_finding_referrals_reports_who_to_ask(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "a.db"))
    init_db()

    with patch.object(referrals_route, "load_profile", return_value=PROFILE), \
         patch.object(referrals_route, "find_referrals", return_value=FOUND) as find:
        resp = client.post("/api/v1/referrals/find", json={"company": "Zepto", "role": "SDE"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["company"] == "Zepto"
    assert body["count"] == 1
    assert body["contacts"][0]["name"] == "Asha Rao"
    assert body["manual_search_url"]
    assert find.call_args.kwargs["role"] == "SDE"


def test_warmth_reasons_arrive_as_a_list_not_raw_json(tmp_path, monkeypatch):
    """The stored column is JSON text; an API client should not have to parse it."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "r.db"))
    init_db()

    with patch.object(referrals_route, "load_profile", return_value=PROFILE), \
         patch.object(referrals_route, "find_referrals", return_value=FOUND):
        contact = client.post("/api/v1/referrals/find", json={"company": "Zepto"}).json()["contacts"][0]

    assert contact["warmth_reasons"] == ["DTU alumni", "1st-degree connection"]


def test_finding_referrals_without_a_profile_says_to_upload_a_resume(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "b.db"))
    init_db()

    with patch.object(referrals_route, "load_profile", return_value=None):
        resp = client.post("/api/v1/referrals/find", json={"company": "Zepto"})

    assert resp.status_code == 400
    assert "resume" in resp.json()["detail"].lower()


def test_listing_returns_saved_contacts_warmest_first(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "c.db"))
    init_db()
    save_contacts([
        {"id": "x1", "name": "Cold", "target_company": "Zepto", "warmth_score": 1,
         "warmth_reasons": '["works there"]'},
        {"id": "x2", "name": "Warm", "target_company": "Zepto", "warmth_score": 5,
         "warmth_reasons": '["alumni"]'},
    ])

    body = client.get("/api/v1/referrals").json()
    assert body["count"] == 2
    assert body["contacts"][0]["name"] == "Warm"
    assert body["contacts"][0]["warmth_reasons"] == ["alumni"]


def test_listing_can_be_filtered_by_company(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "d.db"))
    init_db()
    save_contacts([
        {"id": "y1", "name": "At Zepto", "target_company": "Zepto", "warmth_score": 3},
        {"id": "y2", "name": "At Swiggy", "target_company": "Swiggy", "warmth_score": 3},
    ])

    body = client.get("/api/v1/referrals?company=Swiggy").json()
    assert [c["name"] for c in body["contacts"]] == ["At Swiggy"]


def test_listing_is_empty_before_any_hunt(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "e.db"))
    init_db()
    body = client.get("/api/v1/referrals").json()
    assert body["count"] == 0 and body["contacts"] == []
