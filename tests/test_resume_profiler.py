from unittest.mock import patch
from backend.agents import resume_profiler

FAKE_JSON = '''{
  "personal": {"name": "Manan", "email": "m@x.com"},
  "skills": {"languages": ["Python"], "frameworks": ["FastAPI"]},
  "experience": [{"company": "IndiaMART", "role": "AI Intern"}],
  "education": [{"institution": "DTU", "degree": "B.Tech"}],
  "keywords": ["LangGraph", "RAG"]
}'''

def test_parse_resume_markdown_returns_profile():
    with patch.object(resume_profiler, "complete", return_value=FAKE_JSON):
        profile = resume_profiler.parse_resume_markdown("# Manan ...")
    assert profile.personal.name == "Manan"
    assert "Python" in profile.skills.languages
    assert profile.keywords == ["LangGraph", "RAG"]

def test_parse_strips_markdown_fences():
    fenced = "```json\n" + FAKE_JSON + "\n```"
    with patch.object(resume_profiler, "complete", return_value=fenced):
        profile = resume_profiler.parse_resume_markdown("# Manan ...")
    assert profile.personal.email == "m@x.com"
