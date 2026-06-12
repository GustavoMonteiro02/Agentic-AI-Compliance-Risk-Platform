import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/ai_governance_platform_tests.db"
os.environ["AI_GENERATION_MODE"] = "deterministic"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = ""
os.environ["VECTOR_DB"] = "local"
os.environ["EMBEDDING_PROVIDER"] = "local_hash"

import pytest

from app.database.session import Base, engine, init_db


@pytest.fixture(autouse=True)
def reset_test_database():
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)
