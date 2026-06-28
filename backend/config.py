from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "google/gemini-2.0-flash-exp:free"
    groq_api_key: str | None = None
    db_path: str = "./data/db/career_agent.db"
    profile_path: str = "./data/profile/profile.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
