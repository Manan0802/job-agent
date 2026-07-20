import json
from backend.llm.router import complete
from backend.utils.pdf_parser import pdf_to_markdown
from backend.schemas.profile import Profile

# Spelling the shape out matters: given only a list of top-level key names, the
# model returned `skills` as a flat list and validation failed.
SYSTEM_PROMPT = (
    "You are a precise resume parser. Extract information from the resume text and "
    "return ONLY a valid JSON object. No preamble, no markdown fences, no explanation. "
    "Do not invent data; omit a field or use null when the resume does not state it. "
    "Use exactly this structure:\n"
    "{\n"
    '  "personal": {"name": str, "email": str, "phone": str, "location": str,\n'
    '               "linkedin_url": str, "github_url": str},\n'
    '  "skills": {"languages": [str], "frameworks": [str], "ai_ml": [str],\n'
    '             "tools": [str], "databases": [str]},\n'
    '  "experience": [{"company": str, "role": str, "duration_months": int,\n'
    '                  "highlights": [str], "tech_used": [str]}],\n'
    '  "education": [{"institution": str, "degree": str, "field": str,\n'
    '                 "graduation_year": int}],\n'
    '  "keywords": [str]\n'
    "}\n"
    "`skills` is an object with those five list-valued keys, never a flat list."
)

_MAX_ATTEMPTS = 3


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def parse_resume_markdown(markdown: str) -> Profile:
    """Parse a resume, retrying because model output is not deterministic.

    Live runs produced both truncated JSON and a wrong-shaped `skills` field; a
    fresh attempt usually comes back clean.
    """
    last_error: Exception | None = None
    for _ in range(_MAX_ATTEMPTS):
        try:
            raw = complete(markdown, system=SYSTEM_PROMPT)
            return Profile.model_validate(json.loads(_strip_fences(raw)))
        except Exception as exc:
            last_error = exc
    raise ValueError(
        f"could not parse resume into a profile after {_MAX_ATTEMPTS} attempts: {last_error}"
    )


def parse_resume_pdf(pdf_path: str) -> Profile:
    return parse_resume_markdown(pdf_to_markdown(pdf_path))
