from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_api_key: str = ""
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    llm_model: str = "gemini-3.5-flash"
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "openai/gpt-oss-20b"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    # Unset, providers truncated resume JSON mid-string. Reasoning models spend
    # part of this budget before emitting any answer, so keep it generous.
    llm_max_tokens: int = 8000
    # Groq's free tier caps prompt+completion at 8k tokens/min and rejects the
    # request outright if max_tokens alone would breach it — leave prompt room.
    groq_max_tokens: int = 6000
    db_path: str = "./data/db/career_agent.db"
    profile_path: str = "./data/profile/profile.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
