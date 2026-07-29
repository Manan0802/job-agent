"""Preparing for one interview, without rehearsing things that never happened.

The honesty check matters more here than anywhere else in the app. A resume
line you cannot back is embarrassing; a story you rehearsed and then told out
loud in an interview is worse, because you cannot walk it back.

So a suggested answer that leans on experience the resume never mentions gets
flagged, exactly like a tailoring suggestion does.
"""

import json
import pytest
from unittest.mock import patch

from backend.agents.interview_prep import prepare_for
from backend.llm.errors import ModelUnavailable
from backend.schemas.profile import Education, Experience, Personal, Profile, Skills

JOB = {
    "id": "j1",
    "title": "Backend Engineer",
    "company": "Zepto",
    "description": (
        "Building high-throughput order services. You will own Postgres schema "
        "design and work with Kubernetes for deployment."
    ),
}

PROFILE = Profile(
    personal=Personal(name="Manan Kumar"),
    skills=Skills(languages=["Python"], databases=["Postgres"], frameworks=["FastAPI"]),
    experience=[Experience(
        role="SDE-1", company="IndiaMART",
        highlights=["Cut order API latency by 40% by adding a Postgres index"],
        tech_used=["Python", "Postgres"],
    )],
    education=[Education(institution="DTU", degree="B.Tech", field="Software Engineering")],
)


def _reply(**overrides):
    data = {
        "role_focus": "Whether you can own a Postgres schema under load.",
        "questions": [{
            "question": "Walk me through a query you made faster.",
            "why": "The posting leads on high-throughput order services.",
            "answer_from": "The Postgres index at IndiaMART that cut latency 40%.",
        }],
        "weak_spots": ["Kubernetes — the posting asks for it, your resume does not show it."],
        "ask_them": ["Who owns the schema today?"],
    }
    data.update(overrides)
    return json.dumps(data)


def _returning(text):
    return patch("backend.agents.interview_prep.complete", return_value=text)


def test_it_returns_questions_grounded_in_the_posting():
    with _returning(_reply()):
        prep = prepare_for(JOB, PROFILE)

    assert prep.questions[0].question == "Walk me through a query you made faster."
    assert "high-throughput" in prep.questions[0].why


def test_each_question_says_which_of_your_own_experiences_answers_it():
    """A question list without this is a generic article. The point is knowing
    which real story to rehearse."""
    with _returning(_reply()):
        prep = prepare_for(JOB, PROFILE)

    assert "IndiaMART" in prep.questions[0].answer_from


def test_an_answer_leaning_on_experience_the_resume_lacks_is_flagged():
    reply = _reply(questions=[{
        "question": "How do you deploy?",
        "why": "The posting mentions deployment.",
        "answer_from": "Describe your Kubernetes rollout strategy.",
    }])
    with _returning(reply):
        prep = prepare_for(JOB, PROFILE)

    assert "kubernetes" in prep.questions[0].unsupported
    assert prep.has_unsupported


def test_naming_the_employer_is_not_treated_as_a_false_claim():
    """Flagging the company you are interviewing at would teach the user to
    ignore the warning."""
    reply = _reply(questions=[{
        "question": "Why us?",
        "why": "Standard.",
        "answer_from": "Your Postgres work maps onto what Zepto is building.",
    }])
    with _returning(reply):
        prep = prepare_for(JOB, PROFILE)

    assert prep.questions[0].unsupported == []


def test_an_honest_answer_from_the_resume_is_left_alone():
    with _returning(_reply()):
        prep = prepare_for(JOB, PROFILE)

    assert prep.questions[0].unsupported == []
    assert not prep.has_unsupported


def test_gaps_are_surfaced_rather_than_papered_over():
    """Being asked about something you have not done is the likeliest way an
    interview goes wrong, so it is worth knowing in advance."""
    with _returning(_reply()):
        prep = prepare_for(JOB, PROFILE)

    assert any("Kubernetes" in spot for spot in prep.weak_spots)


def test_it_suggests_what_to_ask_them():
    with _returning(_reply()):
        prep = prepare_for(JOB, PROFILE)

    assert prep.ask_them == ["Who owns the schema today?"]


def test_the_prompt_asks_for_enough_questions_to_be_worth_reading():
    """A real run returned three, because nothing asked for more. Three is not
    preparation for an interview loop."""
    from backend.agents.interview_prep import SYSTEM_PROMPT

    assert "six" in SYSTEM_PROMPT.lower() or "6" in SYSTEM_PROMPT


def test_too_many_questions_are_cut_to_what_can_be_rehearsed():
    many = [{"question": f"Q{i}", "why": "w", "answer_from": "a"} for i in range(20)]
    with _returning(_reply(questions=many)):
        prep = prepare_for(JOB, PROFILE)

    assert len(prep.questions) <= 8


def test_a_fenced_reply_is_still_read():
    with _returning(f"```json\n{_reply()}\n```"):
        prep = prepare_for(JOB, PROFILE)

    assert prep.questions


def test_a_model_that_never_returns_usable_json_says_so():
    with _returning("I'd be happy to help you prepare!"):
        with pytest.raises(ModelUnavailable):
            prepare_for(JOB, PROFILE)


def test_it_retries_before_giving_up():
    with patch(
        "backend.agents.interview_prep.complete",
        side_effect=["nonsense", _reply()],
    ):
        assert prepare_for(JOB, PROFILE).questions
