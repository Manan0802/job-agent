from backend.db.database import get_session, init_db
from backend.db.models import ContactRow
from backend.utils.dedup import contact_id


def test_insert_and_read_contact(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "c.db"))
    init_db()
    cid = contact_id("https://linkedin.com/in/asha-rao", "Asha Rao", "Zepto")

    with get_session() as s:
        s.add(ContactRow(
            id=cid, target_company="Zepto", name="Asha Rao",
            linkedin_url="https://linkedin.com/in/asha-rao",
            current_role="SDE-2", current_company="Zepto", location="Bangalore",
            education='{"college": "DTU", "year": 2021}', degree_type="2nd",
            warmth_score=4, warmth_reasons='["alumni match"]',
            source="search", created_at="2026-07-22",
        ))
        s.commit()

    with get_session() as s:
        row = s.get(ContactRow, cid)
        assert row.name == "Asha Rao"
        assert row.warmth_score == 4
        assert row.outreach_status == "pending"   # every contact starts un-contacted


def test_contact_id_is_stable_and_ignores_cosmetic_differences():
    a = contact_id("https://linkedin.com/in/asha-rao", "Asha Rao", "Zepto")
    b = contact_id("https://linkedin.com/in/asha-rao/", " asha rao ", "zepto")
    assert a == b
    assert len(a) == 64


def test_the_same_person_found_twice_gets_one_id():
    """A contact can arrive from both the CSV and a search; the profile URL is
    the identity."""
    from_csv = contact_id("https://linkedin.com/in/asha-rao", "Asha Rao", "Zepto")
    from_search = contact_id("https://linkedin.com/in/asha-rao", "Asha R.", "Zepto")
    assert from_csv == from_search


def test_contacts_without_a_profile_url_fall_back_to_name_and_company():
    """LinkedIn's CSV export often has no profile URL."""
    a = contact_id(None, "Asha Rao", "Zepto")
    b = contact_id("", "Asha Rao", "Zepto")
    assert a == b
    assert a != contact_id(None, "Asha Rao", "Swiggy")
    assert a != contact_id(None, "Bhavya Rao", "Zepto")
