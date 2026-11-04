"""All settings in one place. Values come from environment variables or backend/.env."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Fantasy Pulse API"

    # llm1: Groq
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"
    # llm2: Gemini
    google_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    # llm3: Aion Labs (OpenAI-compatible API)
    aion_api_key: str | None = None
    aion_model: str = "aion-labs/aion-3.5"
    aion_base_url: str = "https://api.aionlabs.ai/v1"

    # Which LLMs to try, in order. Use e.g. "aion" to test only one.
    llm_order: str = "groq,gemini,aion"
    llm_timeout_s: int = 20

    data_dir: str = str(APP_DIR / "data" / "matches")
    cors_origins: str = "*"               # comma-separated list
    big_swing_threshold: float = 20.0     # fan-point change that triggers the "big swing" branch

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_order_list(self) -> tuple[str, ...]:
        return tuple(o.strip().lower() for o in self.llm_order.split(",") if o.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()