import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/ai_governance_platform_tests.db"
os.environ["AI_GENERATION_MODE"] = "deterministic"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = ""
os.environ["VECTOR_DB"] = "local"
os.environ["EMBEDDING_PROVIDER"] = "local_hash"
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGSMITH_API_KEY"] = ""
os.environ["AUTH_MODE"] = "disabled"
os.environ["PLATFORM_API_KEY"] = ""
os.environ["PLATFORM_API_KEY_SHA256"] = ""
os.environ["DEFAULT_TENANT_ID"] = "default"
os.environ["CORS_ALLOWED_ORIGINS"] = ""
os.environ["API_RATE_LIMIT_PER_MINUTE"] = "0"
os.environ["MCP_TRANSPORT"] = "stdio"

import pytest

from app.database.session import Base, engine, init_db


@pytest.fixture(autouse=True)
def reset_test_database():
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)
