"""Tailoring a resume to one job, without inventing anything.

The whole feature is only useful if the user can trust it: a tool that quietly
adds skills you do not have gets you caught in the interview. So the tests pin
down that experience you *have but buried* is treated differently from
experience you genuinely lack.
"""

import json

import pytest
from unittest.mock import patch

from backend.agents import resume_tailor
from backend.schemas.profile import Education, Experience, Personal, Profile, Skills

PROFILE = Profile(
    personal=Personal(name="Manan Kumar", location="Delhi"),
    skills=Skills(languages=["Python", "C++"], ai_ml=["LangGraph", "RAG"]),
    experience=[Experience(company="IndiaMART", role="AI Engineer",
                           highlights=["Built a RAG pipeline"], tech_used=["LLMs"])],
    education=[Education(institution="DTU", degree="B.Tech")],
)

JOB = {
    "title": "AI Engineer",
    "company": "Zepto",
    "description": "Build distributed RAG pipelines in Python. Kubernetes required.",
}

ANALYSIS = json.dumps({
    "verdict": "Strong fit on the AI work; the infra requirement is the real gap.",
    "strengths": ["Built RAG pipelines, which is the core of this role"],
    "buried": ["LangGraph is listed under skills but never shown in your experience"],
    "missing": ["Kubernetes"],
    "suggestions": [
        {"section": "experience", "change": "Lead the IndiaMART bullet with the RAG pipeline",
         "why": "The posting opens with RAG pipelines"},
    ],
})


def test_returns_a_validated_analysis():
    with patch.object(resume_tailor, "complete", return_value=ANALYSIS):
        fit = resume_tailor.analyze_fit(JOB, PROFILE)

    assert fit.verdict
    assert fit.missing == ["Kubernetes"]
    assert fit.suggestions[0].section == "experience"
    assert fit.suggestions[0].why


def test_the_prompt_carries_the_job_and_the_real_resume():
    with patch.object(resume_tailor, "complete", return_value=ANALYSIS) as c:
        resume_tailor.analyze_fit(JOB, PROFILE)

    prompt = c.call_args[0][0]
    assert "Kubernetes" in prompt          # from the posting
    assert "RAG pipeline" in prompt        # from the resume highlights
    assert "IndiaMART" in prompt


def test_the_prompt_forbids_inventing_experience():
    system = resume_tailor.SYSTEM_PROMPT.lower()
    assert "invent" in system or "fabricate" in system
    assert "already" in system             # rewrite what is already true


def test_the_prompt_separates_what_is_buried_from_what_is_absent():
    """This distinction is the whole point; without it the model conflates them."""
    system = resume_tailor.SYSTEM_PROMPT.lower()
    assert "buried" in system
    assert "missing" in system


def test_every_suggestion_has_to_justify_itself_against_the_posting():
    with patch.object(resume_tailor, "complete", return_value=ANALYSIS):
        fit = resume_tailor.analyze_fit(JOB, PROFILE)

    for suggestion in fit.suggestions:
        assert suggestion.change and suggestion.why


def test_malformed_output_is_retried():
    with patch.object(resume_tailor, "complete", side_effect=['{"verdict": "cut', ANALYSIS]) as c:
        assert resume_tailor.analyze_fit(JOB, PROFILE).verdict
    assert c.call_count == 2


def test_a_model_that_never_complies_fails_loudly():
    with patch.object(resume_tailor, "complete", return_value="not json"):
        with pytest.raises(ValueError, match="could not analyse"):
            resume_tailor.analyze_fit(JOB, PROFILE)


def test_analysis_asks_for_a_sensible_token_budget():
    with patch.object(resume_tailor, "complete", return_value=ANALYSIS) as c:
        resume_tailor.analyze_fit(JOB, PROFILE)
    assert 0 < c.call_args.kwargs["max_tokens"] <= 3000


STRETCH = json.dumps({
    "verdict": "Weak fit.",
    "strengths": [], "buried": [], "missing": ["Kubernetes"],
    "suggestions": [
        # Real output: the model lifted "distributed" straight from the posting,
        # even though that word appears nowhere in the resume.
        {"section": "summary",
         "change": "Add: Experienced in building distributed, scalable backend systems",
         "why": "The posting emphasises distributed systems"},
        {"section": "experience",
         "change": "Lead with the RAG pipeline you built at IndiaMART",
         "why": "The posting opens with RAG"},
    ],
})


def test_a_suggestion_that_borrows_a_claim_from_the_posting_is_flagged():
    """Prompting alone did not stop this, so it is checked in code."""
    with patch.object(resume_tailor, "complete", return_value=STRETCH):
        fit = resume_tailor.analyze_fit(JOB, PROFILE)

    stretched, grounded = fit.suggestions
    assert "distributed" in [t.lower() for t in stretched.unsupported]
    assert grounded.unsupported == []


def test_a_suggestion_reusing_your_own_words_is_not_flagged():
    with patch.object(resume_tailor, "complete", return_value=ANALYSIS):
        fit = resume_tailor.analyze_fit(JOB, PROFILE)

    assert all(s.unsupported == [] for s in fit.suggestions)


def test_the_analysis_says_whether_anything_was_flagged():
    with patch.object(resume_tailor, "complete", return_value=STRETCH):
        assert resume_tailor.analyze_fit(JOB, PROFILE).has_unsupported is True

    with patch.object(resume_tailor, "complete", return_value=ANALYSIS):
        assert resume_tailor.analyze_fit(JOB, PROFILE).has_unsupported is False


COVER_LETTER = json.dumps({
    "body": "Dear hiring team,\n\nI built a RAG pipeline at IndiaMART...\n\nManan Kumar",
    "opening_hook": "the RAG pipeline work",
})


def test_a_cover_letter_is_drafted_from_the_same_facts():
    with patch.object(resume_tailor, "complete", return_value=COVER_LETTER):
        letter = resume_tailor.draft_cover_letter(JOB, PROFILE)

    assert "IndiaMART" in letter.body
    assert letter.opening_hook


def test_the_cover_letter_prompt_also_forbids_invention():
    assert "invent" in resume_tailor.COVER_LETTER_PROMPT.lower()


def test_the_cover_letter_prompt_keeps_it_short():
    """A page of prose does not get read."""
    assert "words" in resume_tailor.COVER_LETTER_PROMPT.lower()


def test_a_cover_letter_is_checked_for_overreach_too():
    """The letter goes straight to the employer, so it gets the same check the
    resume suggestions get."""
    stretched = json.dumps({
        "body": "I have deep Kubernetes experience and built distributed systems.",
        "opening_hook": "the infra work",
    })
    with patch.object(resume_tailor, "complete", return_value=stretched):
        letter = resume_tailor.draft_cover_letter(JOB, PROFILE)

    assert "kubernetes" in [t.lower() for t in letter.unsupported]
    assert letter.has_unsupported is True


def test_a_grounded_cover_letter_is_not_flagged():
    with patch.object(resume_tailor, "complete", return_value=COVER_LETTER):
        letter = resume_tailor.draft_cover_letter(JOB, PROFILE)

    assert letter.unsupported == []
    assert letter.has_unsupported is False


def test_naming_the_company_and_role_is_not_treated_as_overreach():
    """Addressing the letter to the company is expected, not a claim. Flagging
    it would train the user to ignore the warning."""
    named = json.dumps({
        "body": "I'd love to join Zepto as an AI Engineer. I built RAG pipelines at IndiaMART.",
        "opening_hook": "the RAG work",
    })
    with patch.object(resume_tailor, "complete", return_value=named):
        letter = resume_tailor.draft_cover_letter(JOB, PROFILE)

    flagged = [t.lower() for t in letter.unsupported]
    assert "zepto" not in flagged
    assert "engineer" not in flagged
