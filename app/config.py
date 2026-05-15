from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    gemini_api_key: str = ""

    llm_provider: str = "anthropic"      # "anthropic" | "gemini"
    gemini_model: str = "gemini-2.5-flash"

    openai_api_key: str = ""
    voyage_api_key: str = ""

    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"

    database_url: str = "postgresql://grc:grc_secret@localhost:5432/grc_db"
    claude_model: str = "claude-sonnet-4-5"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
