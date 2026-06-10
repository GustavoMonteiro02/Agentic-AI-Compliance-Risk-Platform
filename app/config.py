from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Governance & Compliance Intelligence Platform"
    database_url: str = "sqlite:///./ai_governance.db"
    knowledge_base_path: Path = Path("data")
    ai_generation_mode: str = "deterministic"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "ai-governance-compliance-platform"
    vector_db: str = "local"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "ai_governance_requirements"
    embedding_provider: str = "local_hash"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 128
    auth_mode: str = "disabled"
    platform_api_key: str | None = None
    default_user_role: str = "admin"
    default_tenant_id: str = "default"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
