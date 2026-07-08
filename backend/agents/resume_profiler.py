import json
from backend.llm.router import complete
from backend.utils.pdf_parser import pdf_to_markdown
from backend.schemas.profile import Profile

SYSTEM_PROMPT = (
    "You are a precise resume parser. Extract information from the resume text and "
    "return ONLY a valid JSON object. No preamble, no markdown fences, no explanation. "
    "Use these top-level keys: personal, skills, experience, education, keywords. "
    "If a field is missing, omit it or use null. Do not invent data."
)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def parse_resume_markdown(markdown: str) -> Profile:
    raw = complete(markdown, system=SYSTEM_PROMPT)
    data = json.loads(_strip_fences(raw))
    return Profile.model_validate(data)


def parse_resume_pdf(pdf_path: str) -> Profile:
    return parse_resume_markdown(pdf_to_markdown(pdf_path))
