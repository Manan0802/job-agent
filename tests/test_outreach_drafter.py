"""Drafting the actual outreach message.

This is the part the user's reputation rides on, so the tests pin down what
goes into the prompt (real personalization, never invented credentials) and
that malformed model output never reaches them.
"""

import json

import pytest
from unittest.mock import patch

from backend.agents import outreach_drafter
from backend.schemas.profile import Education, Experience, Personal, Profile, Skills

PROFILE = Profile(
    personal=Personal(name="Manan Kumar", email="manan@x.com", location="Delhi"),
    skills=Skills(languages=["Python"], ai_ml=["LangGraph", "RAG"]),
    experience=[Experience(company="IndiaMART", role="AI Engineer", tech_used=["LLMs"])],
    education=[Education(institution="Delhi Technological University (DTU)",
                         degree="B.Tech", graduation_year=2026)],
)

CONTACT = {
    "name": "Asha Rao", "current_company": "Zepto", "current_role": "SDE-2",
    "linkedin_url": "https://linkedin.com/in/asha-rao", "degree_type": "1st",
    "warmth_score": 5, "warmth_reasons": ["DTU alumni", "already a 1st-degree connection"],
}

JOB = {"title": "SDE-2 Backend", "company": "Zepto",
       "url": "https://zepto.com/jobs/1", "description": "Build backend systems"}

GOOD = json.dumps({
    "subject": None,
    "message": "Hey Asha! Saw we both went through DTU. I'm an AI engineer at "
               "IndiaMART working on LangGraph systems, and Zepto's SDE-2 Backend "
               "role looks like a great fit. Would you be open to referring me? "
               "No pressure at all if the timing isn't right.",
    "tone": "casual",
    "personalization_elements": ["DTU alumni", "both engineers"],
})


def test_returns_a_validated_draft():
    with patch.object(outreach_drafter, "complete", return_value=GOOD):
        draft = outreach_drafter.draft_message(CONTACT, PROFILE, job=JOB)

    assert draft.message.startswith("Hey Asha")
    assert draft.tone == "casual"
    assert "DTU alumni" in draft.personalization_elements
    assert draft.word_count > 0          # derived, never trusted from the model


def test_the_prompt_carries_the_real_people_and_the_real_job():
    with patch.object(outreach_drafter, "complete", return_value=GOOD) as c:
        outreach_drafter.draft_message(CONTACT, PROFILE, job=JOB)

    prompt = c.call_args[0][0]
    assert "Asha Rao" in prompt and "Zepto" in prompt
    assert "Manan Kumar" in prompt
    assert "SDE-2 Backend" in prompt


def test_the_prompt_carries_why_this_contact_was_picked():
    """The warmth reasons are the genuine connection point to open with."""
    with patch.object(outreach_drafter, "complete", return_value=GOOD) as c:
        outreach_drafter.draft_message(CONTACT, PROFILE, job=JOB)

    assert "DTU alumni" in c.call_args[0][0]


def test_the_rules_that_keep_it_from_reading_like_spam_are_in_the_prompt():
    system = outreach_drafter.SYSTEM_PROMPT.lower()
    assert "sycophantic" in system or "flatter" in system
    assert "no pressure" in system
    assert "invent" in system or "only facts" in system     # no fabricated credentials


def test_a_message_to_a_stranger_is_shorter_than_a_referral_ask():
    cold = outreach_drafter.MESSAGE_TYPES["cold_intro"]
    referral = outreach_drafter.MESSAGE_TYPES["referral_request"]
    assert cold["max_words"] < referral["max_words"]


def test_an_email_gets_a_subject_and_a_dm_does_not():
    email_json = json.dumps({**json.loads(GOOD), "subject": "Quick question about Zepto"})

    with patch.object(outreach_drafter, "complete", return_value=email_json):
        email = outreach_drafter.draft_message(CONTACT, PROFILE, job=JOB,
                                               message_type="email_outreach")
    with patch.object(outreach_drafter, "complete", return_value=GOOD):
        dm = outreach_drafter.draft_message(CONTACT, PROFILE, job=JOB,
                                            message_type="referral_request")

    assert email.channel == "email" and email.subject
    assert dm.channel == "linkedin_dm" and dm.subject is None


def test_an_alumni_connection_gets_the_alumni_opener_by_default():
    assert outreach_drafter.pick_message_type(CONTACT) == "alumni_dm"


def test_a_stranger_gets_a_cold_intro_by_default():
    stranger = {**CONTACT, "degree_type": "2nd", "warmth_score": 1,
                "warmth_reasons": ["works at Zepto"]}
    assert outreach_drafter.pick_message_type(stranger) == "cold_intro"


def test_a_connection_you_share_no_college_with_still_gets_a_referral_ask():
    connection = {**CONTACT, "warmth_reasons": ["already a 1st-degree connection"]}
    assert outreach_drafter.pick_message_type(connection) == "referral_request"


def test_a_follow_up_reminds_without_repeating_the_whole_pitch():
    assert outreach_drafter.MESSAGE_TYPES["followup"]["max_words"] <= 100


def test_every_opener_that_targets_a_role_actually_asks_for_the_referral():
    """A first real draft came back asking only for a chat. The whole point of
    the feature is the referral, so the ask has to be in the brief."""
    for name in ("referral_request", "alumni_dm", "cold_intro", "email_outreach"):
        assert "refer" in outreach_drafter.MESSAGE_TYPES[name]["intent"].lower(), name


def test_dms_are_told_not_to_sign_off_like_an_email():
    """Drafts were closing DMs with 'Best,\\nManan', which reads as a template."""
    assert "sign-off" in outreach_drafter.SYSTEM_PROMPT.lower()


def test_malformed_model_output_is_retried():
    with patch.object(outreach_drafter, "complete",
                      side_effect=['{"message": "cut off mid-', GOOD]) as c:
        draft = outreach_drafter.draft_message(CONTACT, PROFILE, job=JOB)

    assert draft.message.startswith("Hey Asha")
    assert c.call_count == 2


def test_a_model_that_never_complies_fails_loudly():
    with patch.object(outreach_drafter, "complete", return_value="not json"):
        with pytest.raises(ValueError, match="could not draft"):
            outreach_drafter.draft_message(CONTACT, PROFILE, job=JOB)


def test_drafting_asks_for_only_as_many_tokens_as_a_message_needs():
    """Groq counts max_tokens toward its per-minute admission budget."""
    with patch.object(outreach_drafter, "complete", return_value=GOOD) as c:
        outreach_drafter.draft_message(CONTACT, PROFILE, job=JOB)

    assert 0 < c.call_args.kwargs["max_tokens"] <= 2000


def test_drafting_works_without_a_specific_job():
    """Reaching out about a company generally, before a role is picked."""
    with patch.object(outreach_drafter, "complete", return_value=GOOD):
        draft = outreach_drafter.draft_message(CONTACT, PROFILE)
    assert draft.message
