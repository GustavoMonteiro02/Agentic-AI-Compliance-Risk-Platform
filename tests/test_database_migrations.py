from sqlalchemy import create_engine, inspect, text

from app.database.migrations import apply_database_migrations, migration_status


def test_database_migrations_add_missing_columns_to_existing_tables(tmp_path):
    db_path = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE evidence_items (id VARCHAR PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE ai_systems (id VARCHAR PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE ai_system_profiles (id VARCHAR PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE risk_assessments (id VARCHAR PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE audit_events (id VARCHAR PRIMARY KEY)"))

    result = apply_database_migrations(engine)
    inspector = inspect(engine)

    evidence_columns = {column["name"] for column in inspector.get_columns("evidence_items")}
    system_columns = {column["name"] for column in inspector.get_columns("ai_systems")}
    assert result["current"] is True
    assert "20260610_001_evidence_lifecycle" in result["applied"]
    assert {"due_date", "expires_at", "approved_by", "approved_at", "review_notes"}.issubset(evidence_columns)
    assert "tenant_id" in system_columns
    assert migration_status(engine)["pending"] == []


def test_runtime_readiness_reports_database_migration_state():
    from fastapi.testclient import TestClient

    from app.api.main import app

    response = TestClient(app).get("/runtime/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["checks"]["database_migrations"]["current"] is True
    assert payload["checks"]["database_migrations"]["pending"] == []
