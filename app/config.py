from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    gemini_api_key: str = ""

    llm_provider: str = "anthropic"      # "anthropic" | "gemini"
    gemini_model: str = "gemini-2.5-flash"

    openai_api_key: str = ""
    voyage_api_key: str = ""

    embedding_provider: str = "voyage"
    embedding_model: str = "voyage-3"

    database_url: str
    claude_model: str = "claude-sonnet-4-5"
    jwt_secret_key: str

    # Free-tier fallback LLM providers (all optional)
    groq_api_key: str = ""
    cerebras_api_key: str = ""
    openrouter_api_key: str = ""

    # Local Ollama fallback (install: brew install ollama && ollama pull llama3.2)
    ollama_model: str = "llama3.2"

    # Email — Resend
    resend_api_key: str = ""
    resend_from_email: str = "onboarding@resend.dev"

    # App URL — used in emails (change to production domain before deploying)
    app_url: str = "http://localhost:5173"

    # CORS — comma-separated list of allowed frontend origins
    # Dev default allows Vite dev server. In production set to your real domain.
    # e.g. ALLOWED_ORIGINS=https://sentinel.yourdomain.com
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Set to true in production once HTTPS is live — enables HSTS header
    https_only: bool = False

    # S3-compatible file storage (AWS S3, Cloudflare R2, MinIO)
    # Leave blank to store files in Postgres (dev/local only)
    s3_bucket: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "auto"
    s3_endpoint_url: str = ""  # blank = AWS; set to R2 endpoint for Cloudflare

    # Sentry — set SENTRY_DSN in .env to enable error tracking
    sentry_dsn: str = ""

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
