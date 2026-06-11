from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Governance & Compliance Intelligence Platform"
    database_url: str = "sqlite:///./ai_governance.db"
    knowledge_base_path: Path = Path("data")
    ai_generation_mode: str = "deterministic"
    llm_provider: str = "openai"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"
    openai_timeout_seconds: int = 60
    openai_max_retries: int = 2
    openai_max_tokens: int = 2000
    anthropic_api_key: str | None = None
    anthropic_base_url: str = "https://api.anthropic.com/v1"
    anthropic_model: str = "claude-3-5-sonnet-latest"
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_api_url: str = "https://api.smith.langchain.com"
    langsmith_project: str = "ai-governance-compliance-platform"
    vector_db: str = "local"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "ai_governance_requirements"
    pinecone_api_key: str | None = None
    pinecone_index_host: str | None = None
    pinecone_namespace: str = "ai-governance-requirements"
    embedding_provider: str = "local_hash"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 128
    auth_mode: str = "disabled"
    platform_api_key: str | None = None
    default_user_role: str = "admin"
    default_tenant_id: str = "default"
    cors_allowed_origins: str = ""
    security_headers_enabled: bool = True
    security_hsts_enabled: bool = False
    max_request_body_bytes: int = 1_048_576
    api_rate_limit_per_minute: int = 0
    mcp_server_name: str = "ai-governance-compliance"
    mcp_transport: str = "stdio"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 9000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
