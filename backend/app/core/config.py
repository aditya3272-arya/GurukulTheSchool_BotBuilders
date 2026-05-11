from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    app_base_url: str = "http://127.0.0.1:8000"
    serve_frontend: bool = True

    school_id: str

    session_secret: str
    session_max_age_seconds: int = 60 * 60 * 24

    supabase_url: str
    supabase_service_role_key: str
    supabase_postgrest_timeout_seconds: float = Field(default=40.0, ge=5.0, le=120.0)

    groq_api_key: str | None = None
    groq_model_intent: str = "llama-3.1-8b-instant"
    groq_model_answer: str = "llama-3.1-8b-instant"

    gemini_api_key: str | None = None
    gemini_model_intent: str = "gemini-2.5-flash"
    gemini_model_answer: str = "gemini-2.5-flash"

    cerebras_api_key: str | None = None
    cerebras_model_intent: str = "llama3.1-8b"
    cerebras_model_answer: str = "llama-3.3-70b"


settings = Settings()