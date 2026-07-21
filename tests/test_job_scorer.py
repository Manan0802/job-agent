import json
import pytest
from unittest.mock import patch

from backend.agents import job_scorer
from backend.schemas.profile import Profile, Personal, Skills, Experience

PROFILE = Profile(
    personal=Personal(name="Manan", email="m@x.com"),
    skills=Skills(languages=["Python"], ai_ml=["LangGraph", "RAG"]),
    experience=[Experience(company="IndiaMART", role="AI Engineer", tech_used=["LLMs"])],
    keywords=["vector search"],
)

JOB = {
    "title": "AI Engineer",
    "company": "Zepto",
    "location": "Bangalore",
    "description": "Build RAG pipelines with Python and LangGraph.",
}

GOOD = json.dumps({
    "score": 87,
    "reasoning": "Strong overlap on RAG and LangGraph.",
    "matched_skills": ["Python", "LangGraph"],
    "missing_skills": ["Kubernetes"],
})


def test_score_job_returns_validated_score():
    with patch.object(job_scorer, "complete", return_value=GOOD):
        result = job_scorer.score_job(JOB, PROFILE)
    assert result.score == 87
    assert "LangGraph" in result.matched_skills
    assert result.reasoning


def test_score_job_strips_markdown_fences():
    with patch.object(job_scorer, "complete", return_value=f"```json\n{GOOD}\n```"):
        assert job_scorer.score_job(JOB, PROFILE).score == 87


def test_prompt_carries_both_the_job_and_the_candidate():
    with patch.object(job_scorer, "complete", return_value=GOOD) as c:
        job_scorer.score_job(JOB, PROFILE)
    prompt = c.call_args[0][0]
    assert "AI Engineer" in prompt and "Zepto" in prompt
    assert "LangGraph" in prompt and "Python" in prompt


def test_score_job_retries_on_malformed_output():
    """Live models return truncated JSON often enough to matter."""
    with patch.object(job_scorer, "complete", side_effect=['{"score": 8', GOOD]) as c:
        assert job_scorer.score_job(JOB, PROFILE).score == 87
    assert c.call_count == 2


def test_score_job_rejects_out_of_range_score_then_retries():
    off_scale = json.dumps({"score": 950, "reasoning": "oops"})
    with patch.object(job_scorer, "complete", side_effect=[off_scale, GOOD]) as c:
        assert job_scorer.score_job(JOB, PROFILE).score == 87
    assert c.call_count == 2


def test_score_job_raises_actionable_error_when_model_never_complies():
    with patch.object(job_scorer, "complete", return_value="not json at all"):
        with pytest.raises(ValueError, match="could not score"):
            job_scorer.score_job(JOB, PROFILE)


def test_score_jobs_attaches_scores_to_each_job():
    jobs = [dict(JOB, title="AI Engineer"), dict(JOB, title="ML Engineer")]
    with patch.object(job_scorer, "complete", return_value=GOOD):
        scored = job_scorer.score_jobs(jobs, PROFILE)
    assert len(scored) == 2
    assert all(j["llm_score"] == 87 for j in scored)
    assert all(json.loads(j["llm_breakdown"])["matched_skills"] for j in scored)


def test_score_jobs_keeps_going_when_one_job_fails():
    """One unscoreable job must not throw away the whole run's LLM spend."""
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] <= job_scorer._MAX_ATTEMPTS:   # first job exhausts its retries
            raise RuntimeError("rate limited")
        return GOOD

    with patch.object(job_scorer, "complete", side_effect=flaky):
        scored = job_scorer.score_jobs([dict(JOB), dict(JOB, title="Other")], PROFILE)

    assert len(scored) == 2
    assert scored[0]["llm_score"] == 87          # the job that scored fine
    assert scored[1]["llm_score"] is None        # failed, kept but ranked last


def test_score_jobs_sorts_best_first():
    low = json.dumps({"score": 40, "reasoning": "weak"})
    high = json.dumps({"score": 90, "reasoning": "strong"})
    with patch.object(job_scorer, "complete", side_effect=[low, high]):
        scored = job_scorer.score_jobs([dict(JOB, title="Weak"), dict(JOB, title="Strong")], PROFILE)
    assert [j["title"] for j in scored] == ["Strong", "Weak"]


def test_score_jobs_empty_list():
    assert job_scorer.score_jobs([], PROFILE) == []
