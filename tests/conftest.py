import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/ai_governance_platform_tests.db"

import pytest

from app.database.session import Base, engine, init_db


@pytest.fixture(autouse=True)
def reset_test_database():
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)

