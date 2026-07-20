"""Regression tests for real failures seen parsing an actual resume.

Both bugs below were invisible to the mocked happy-path tests and only showed up
against live Gemini/Groq responses.
"""

import pytest
from unittest.mock import patch

from backend.agents import resume_profiler

GOOD_JSON = '''{
  "personal": {"name": "Manan", "email": "m@x.com"},
  "skills": {"languages": ["Python"]},
  "experience": [], "education": [], "keywords": []
}'''

# The model returned this shape for real: skills as a flat list, not the nested object.
WRONG_SHAPE_JSON = '{"personal": {"name": "Manan"}, "skills": ["Python", "C++"]}'

# Real Groq output truncated mid-string when max_tokens was unset.
TRUNCATED_JSON = '{"personal": {"name": "Manan"}, "keywords": ["AI", "R'


def test_system_prompt_specifies_nested_skills_shape():
    """A vague prompt is what made the model emit skills as a flat list."""
    prompt = resume_profiler.SYSTEM_PROMPT
    for key in ("languages", "frameworks", "ai_ml", "tools", "databases"):
        assert key in prompt, f"prompt must pin down skills.{key}"


def test_parse_retries_after_truncated_json():
    with patch.object(resume_profiler, "complete", side_effect=[TRUNCATED_JSON, GOOD_JSON]) as c:
        profile = resume_profiler.parse_resume_markdown("# resume")
    assert profile.personal.name == "Manan"
    assert c.call_count == 2


def test_parse_retries_after_wrong_schema_shape():
    with patch.object(resume_profiler, "complete", side_effect=[WRONG_SHAPE_JSON, GOOD_JSON]) as c:
        profile = resume_profiler.parse_resume_markdown("# resume")
    assert "Python" in profile.skills.languages
    assert c.call_count == 2


def test_parse_raises_actionable_error_when_model_never_complies():
    with patch.object(resume_profiler, "complete", return_value=TRUNCATED_JSON):
        with pytest.raises(ValueError, match="could not parse"):
            resume_profiler.parse_resume_markdown("# resume")


def test_parse_succeeds_first_try_without_retrying():
    with patch.object(resume_profiler, "complete", return_value=GOOD_JSON) as c:
        resume_profiler.parse_resume_markdown("# resume")
    assert c.call_count == 1
