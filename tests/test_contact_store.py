from backend.db.database import init_db
from backend.services.contact_store import load_contacts, save_contacts
from backend.utils.dedup import contact_id


def _contact(name="Asha Rao", company="Zepto", **extra):
    return {
        "id": contact_id(f"https://linkedin.com/in/{name.lower().replace(' ', '-')}",
                         name, company),
        "target_company": company, "name": name,
        "linkedin_url": f"https://linkedin.com/in/{name.lower().replace(' ', '-')}",
        "current_role": "SDE-2", "current_company": company, "location": "Bangalore",
        "degree_type": "2nd", "warmth_score": 3, "warmth_reasons": '["works there"]',
        "source": "search", "created_at": "2026-07-22", **extra,
    }


def test_saves_and_reads_back_contacts(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "a.db"))
    init_db()
    save_contacts([_contact()])

    contacts = load_contacts("Zepto")
    assert len(contacts) == 1
    assert contacts[0]["name"] == "Asha Rao"
    assert contacts[0]["warmth_score"] == 3


def test_rerunning_a_hunt_updates_instead_of_duplicating(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "b.db"))
    init_db()
    save_contacts([_contact(warmth_score=2)])
    save_contacts([_contact(warmth_score=5)])

    contacts = load_contacts("Zepto")
    assert len(contacts) == 1
    assert contacts[0]["warmth_score"] == 5


def test_a_rerun_never_resets_who_you_already_messaged(tmp_path, monkeypatch):
    """Outreach status is owned by the outreach flow, not the contact hunt."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "c.db"))
    init_db()
    save_contacts([_contact(outreach_status="sent")])
    save_contacts([_contact()])                     # a later hunt, no status set

    assert load_contacts("Zepto")[0]["outreach_status"] == "sent"


def test_contacts_come_back_warmest_first(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "d.db"))
    init_db()
    save_contacts([
        _contact(name="Cold One", warmth_score=1),
        _contact(name="Warm One", warmth_score=5),
        _contact(name="Mild One", warmth_score=3),
    ])

    assert [c["name"] for c in load_contacts("Zepto")] == ["Warm One", "Mild One", "Cold One"]


def test_contacts_are_scoped_to_their_company(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "e.db"))
    init_db()
    save_contacts([_contact(name="At Zepto", company="Zepto"),
                   _contact(name="At Swiggy", company="Swiggy")])

    assert [c["name"] for c in load_contacts("Zepto")] == ["At Zepto"]
    assert len(load_contacts()) == 2       # no filter returns everything


def test_saving_nothing_is_harmless(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "f.db"))
    init_db()
    save_contacts([])
    assert load_contacts() == []
