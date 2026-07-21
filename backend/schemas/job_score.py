from pydantic import BaseModel, Field


class JobScore(BaseModel):
    """How well one job fits the candidate, as judged by the LLM."""

    score: float = Field(ge=0, le=100)
    reasoning: str = ""
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
