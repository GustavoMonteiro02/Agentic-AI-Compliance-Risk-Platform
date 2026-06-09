from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Governance & Compliance Intelligence Platform"
    database_url: str = "sqlite:///./ai_governance.db"
    knowledge_base_path: Path = Path("data")
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()

