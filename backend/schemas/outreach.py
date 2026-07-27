from pydantic import BaseModel, Field


class OutreachDraft(BaseModel):
    """A message the user will review before anything is sent."""

    message: str
    subject: str | None = None
    tone: str = "professional"
    personalization_elements: list[str] = Field(default_factory=list)
    message_type: str = "referral_request"
    channel: str = "linkedin_dm"

    @property
    def word_count(self) -> int:
        return len(self.message.split())
