"""Warmth scoring ranks who is most likely to actually refer you.

The PRD's table is written around one candidate ("DTU alumni", "Delhi-based").
Here those come from the user's own profile instead, so the scoring works for
any user rather than only the author.
"""

from backend.schemas.profile import Education, Experience, Personal, Profile, Skills
from backend.services.warmth import score_contact

PROFILE = Profile(
    personal=Personal(name="Manan", location="Delhi, India"),
    skills=Skills(languages=["Python"], ai_ml=["LangGraph"]),
    experience=[Experience(company="IndiaMART", role="AI Engineer", tech_used=["RAG"])],
    education=[Education(institution="Delhi Technological University", degree="B.Tech",
                         graduation_year=2026)],
)


def _contact(**overrides) -> dict:
    return {
        "name": "Asha Rao", "current_company": "Zepto", "current_role": "SDE-1",
        "location": "Bangalore, India", "education": None, "degree_type": "2nd",
        **overrides,
    }


def test_alumni_who_is_already_a_connection_scores_highest():
    score, reasons = score_contact(
        _contact(degree_type="1st", education="Delhi Technological University"), PROFILE)
    assert score == 5
    assert any("alumni" in r.lower() for r in reasons)
    assert any("connection" in r.lower() for r in reasons)


def test_alumni_you_do_not_know_yet_scores_just_below():
    score, _ = score_contact(
        _contact(degree_type="2nd", education="Delhi Technological University"), PROFILE)
    assert score == 4


def test_a_plain_connection_scores_mid():
    score, reasons = score_contact(_contact(degree_type="1st"), PROFILE)
    assert score == 3
    assert any("connection" in r.lower() for r in reasons)


def test_a_stranger_at_the_company_is_a_cold_intro():
    score, reasons = score_contact(_contact(), PROFILE)
    assert score == 1
    assert reasons


def test_seniority_makes_a_stranger_worth_contacting():
    """Someone senior enough to actually make a referral beats a random hire."""
    for title in ("SDE-2", "SDE3", "Engineering Manager", "Tech Lead", "Staff Engineer"):
        score, _ = score_contact(_contact(current_role=title), PROFILE)
        assert score >= 2, title


def test_shared_tech_stack_makes_a_stranger_worth_contacting():
    score, reasons = score_contact(
        _contact(current_role="Engineer", education="Some College",
                 headline="Building RAG pipelines in Python"), PROFILE)
    assert score >= 2
    assert any("python" in r.lower() or "stack" in r.lower() for r in reasons)


def test_the_alma_mater_comes_from_the_profile_not_a_hardcoded_college():
    other_user = Profile(education=[Education(institution="IIT Bombay")])
    iitb_contact = _contact(education="IIT Bombay", degree_type="2nd")

    assert score_contact(iitb_contact, other_user)[0] == 4
    assert score_contact(iitb_contact, PROFILE)[0] < 4    # not Manan's college


def test_a_shared_past_employer_raises_the_score():
    base, _ = score_contact(_contact(degree_type="1st"), PROFILE)
    warmer, reasons = score_contact(
        _contact(degree_type="1st", headline="ex-IndiaMART, now at Zepto"), PROFILE)
    assert warmer > base
    assert any("indiamart" in r.lower() for r in reasons)


def test_scores_never_leave_the_one_to_five_range():
    hottest = _contact(degree_type="1st", education="Delhi Technological University",
                       current_role="Engineering Manager",
                       headline="ex-IndiaMART, Python and LangGraph")
    score, _ = score_contact(hottest, PROFILE)
    assert 1 <= score <= 5


def test_a_profile_with_nothing_filled_in_still_scores():
    score, reasons = score_contact(_contact(), Profile())
    assert 1 <= score <= 5
    assert reasons


def test_every_score_comes_with_its_reasons():
    """The user has to be able to see why someone was ranked first."""
    for contact in (_contact(), _contact(degree_type="1st"),
                    _contact(education="Delhi Technological University")):
        _, reasons = score_contact(contact, PROFILE)
        assert reasons and all(isinstance(r, str) and r for r in reasons)
