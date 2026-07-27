"""Regression tests from scoring real contacts against the real parsed resume.

Every case here scored wrong with tidy fixture data and only surfaced once the
institution and employer strings came back messy from an actual resume.
"""

from backend.schemas.profile import Education, Experience, Personal, Profile, Skills
from backend.services.warmth import score_contact

# Exactly what the resume parser returns — acronym inline, campus city appended.
REAL = Profile(
    personal=Personal(name="Manan Kumar", location="Delhi"),
    skills=Skills(languages=["C", "C++", "Python"], ai_ml=["LangGraph", "RAG"]),
    experience=[
        Experience(company="Bachatt Trusave Fintech", role="SDE-1"),
        Experience(company="IndiaMART InterMESH Ltd", role="AI Engineer"),
    ],
    education=[Education(institution="Delhi Technological University (DTU), New Delhi",
                         degree="B.Tech")],
)


def _contact(**overrides) -> dict:
    return {"name": "X", "current_company": "Zepto", "current_role": "SDE-1",
            "degree_type": "2nd", **overrides}


def test_alumni_matches_when_the_contact_writes_only_the_acronym():
    """Profiles say 'DTU Delhi', not the full registered university name."""
    score, reasons = score_contact(
        _contact(degree_type="1st", education="DTU Delhi"), REAL)
    assert score == 5, reasons


def test_alumni_matches_when_the_contact_writes_the_full_name():
    score, reasons = score_contact(
        _contact(headline="Delhi Technological University alum"), REAL)
    assert score == 4, reasons


def test_a_one_letter_language_does_not_match_any_word_containing_it():
    """'C' in the skill list was matching 'Recruiter'."""
    score, reasons = score_contact(_contact(current_role="Recruiter"), REAL)
    assert not any("stack" in r.lower() for r in reasons), reasons
    assert score == 1


def test_a_one_letter_language_still_matches_when_written_as_a_word():
    _, reasons = score_contact(_contact(headline="Systems programmer in C and Rust"), REAL)
    assert any("stack" in r.lower() for r in reasons), reasons


def test_shared_employer_matches_despite_the_legal_suffix():
    """The resume says 'IndiaMART InterMESH Ltd'; profiles say 'ex-IndiaMART'."""
    _, reasons = score_contact(
        _contact(headline="ex-IndiaMART, now building at Zepto"), REAL)
    assert any("indiamart" in r.lower() for r in reasons), reasons


def test_seniority_separates_people_you_already_know():
    """The LinkedIn export carries no education, so without this every
    connection ties at the same score and the ranking says nothing. A manager
    can approve a referral; a junior engineer usually cannot."""
    manager, _ = score_contact(
        _contact(degree_type="1st", current_role="Engineering Manager"), REAL)
    junior, _ = score_contact(
        _contact(degree_type="1st", current_role="SDE-1"), REAL)

    assert manager > junior


def test_a_recruiter_stranger_stays_the_coldest_lead():
    ranked = sorted(
        [
            _contact(name="Alum", degree_type="1st", education="DTU Delhi"),
            _contact(name="Manager", current_role="Engineering Manager"),
            _contact(name="Recruiter", current_role="Recruiter"),
        ],
        key=lambda c: -score_contact(c, REAL)[0],
    )
    assert [c["name"] for c in ranked][0] == "Alum"
    assert [c["name"] for c in ranked][-1] == "Recruiter"
