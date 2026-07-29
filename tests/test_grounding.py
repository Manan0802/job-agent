"""The honesty check that both tailoring and interview prep run on model output.

It flags words the answer took from the posting that the resume never backs.
The hard part is not catching claims — it is not crying wolf. A warning that
is wrong most of the time teaches the user to click past it, and then they
miss the real one.
"""

from backend.agents.grounding import unsupported_terms

RESUME = (
    "Name: Manan Kumar\n"
    "Skills listed: Python, Postgres, FastAPI, LangGraph\n"
    "Experience:\n- SDE-1 at IndiaMART\n    · Cut order API latency by 40%\n"
)
POSTING = (
    "Title: Backend Engineer\nCompany: Zepto\n"
    "Posting: You will own Postgres schema design and use Kubernetes and Java "
    "for our distributed order services."
)


def test_a_claim_the_resume_cannot_back_is_flagged():
    text = "Describe your Kubernetes rollout strategy."
    assert "kubernetes" in unsupported_terms(text, RESUME, POSTING)


def test_something_the_resume_does_back_is_left_alone():
    text = "Talk about the Postgres index at IndiaMART."
    assert unsupported_terms(text, RESUME, POSTING) == []


def test_naming_the_employer_is_not_a_claim():
    text = "Explain why Zepto is a fit."
    assert unsupported_terms(text, RESUME, POSTING, job_meta="Zepto Backend Engineer") == []


def test_admitting_you_lack_something_is_not_claiming_it():
    """A real run produced "Acknowledge the lack of Java on the resume" and the
    check flagged `java` — reading an admission as a boast. That is the worst
    kind of false positive, because the advice was exactly right."""
    text = "Acknowledge the lack of Java on the resume."
    assert unsupported_terms(text, RESUME, POSTING) == []


def test_a_claim_that_follows_an_admission_is_still_flagged():
    """The whole sentence must not go unchecked just because it opens humbly —
    that would be an easy way for a real overclaim to slip past."""
    text = "Acknowledge the lack of Java, but emphasise your Kubernetes work."
    assert unsupported_terms(text, RESUME, POSTING) == ["kubernetes"]


def test_other_ways_of_admitting_a_gap_are_understood():
    for admission in (
        "You have no experience with Kubernetes.",
        "Your resume does not show Kubernetes.",
        "You haven't used Kubernetes.",
        "Kubernetes is missing from your background.",
    ):
        assert unsupported_terms(admission, RESUME, POSTING) == [], admission


def test_a_word_absent_from_the_posting_is_not_the_check_s_business():
    """This flags borrowing from the posting, not every unfamiliar word."""
    text = "Mention your Rust hobby project."
    assert unsupported_terms(text, RESUME, POSTING) == []


# --- interview prep asks a narrower question ---
#
# Tailoring suggestions are terse edits, so a lowercase capability claim like
# "distributed" is the whole point. Interview prep is discursive prose about
# the role, where the same rule flagged "about", "high" and "designing" — five
# of six answers, none of them real. What can actually be falsely rehearsed is
# a named technology, so that is all prep checks.

def test_prep_flags_a_named_technology_the_resume_lacks():
    text = "Describe your Kubernetes rollout."
    assert unsupported_terms(text, RESUME, POSTING, named_only=True) == ["kubernetes"]


def test_prep_ignores_ordinary_prose_borrowed_from_the_posting():
    text = "Talk about your design of high-throughput backend order services."
    assert unsupported_terms(text, RESUME, POSTING, named_only=True) == []


def test_prep_does_not_mistake_the_first_word_of_a_sentence_for_a_technology():
    text = "Design work matters here. Schema ownership is the theme."
    assert unsupported_terms(text, RESUME, POSTING, named_only=True) == []


def test_prep_still_respects_an_admission():
    text = "You have no experience with Kubernetes."
    assert unsupported_terms(text, RESUME, POSTING, named_only=True) == []


def test_tailoring_keeps_catching_lowercase_claims():
    """The failure this check was built for: "building distributed, scalable
    backend systems" on a resume that never says distributed."""
    text = "Experienced in building distributed order services."
    assert "distributed" in unsupported_terms(text, RESUME, POSTING)
