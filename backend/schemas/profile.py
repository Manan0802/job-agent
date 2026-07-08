from pydantic import BaseModel, Field


class Personal(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None


class Skills(BaseModel):
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    ai_ml: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)


class Experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration_months: int | None = None
    highlights: list[str] = Field(default_factory=list)
    tech_used: list[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    graduation_year: int | None = None


class Profile(BaseModel):
    personal: Personal = Field(default_factory=Personal)
    skills: Skills = Field(default_factory=Skills)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
