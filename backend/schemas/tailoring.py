from pydantic import BaseModel, Field


class Suggestion(BaseModel):
    """One concrete edit the user can make to their own resume."""

    section: str          # summary | experience | skills | projects | education
    change: str           # what to do
    why: str              # what in the job posting makes this worth doing
    # Words the suggestion borrowed from the posting that the resume never
    # backs up. Filled in by code, because prompting alone did not stop it.
    unsupported: list[str] = Field(default_factory=list)


class FitAnalysis(BaseModel):
    """An honest read on one job.

    `buried` and `missing` are deliberately separate. Things you have but did
    not surface are worth rewriting for; things you genuinely lack are not
    something to paper over, and pretending otherwise gets found out in the
    interview.
    """

    verdict: str
    strengths: list[str] = Field(default_factory=list)
    buried: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    suggestions: list[Suggestion] = Field(default_factory=list)

    @property
    def has_unsupported(self) -> bool:
        """Whether any suggestion asks the user to claim something new."""
        return any(s.unsupported for s in self.suggestions)
