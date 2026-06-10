from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _connect_args(database_url: str) -> dict[str, bool]:
    return {"check_same_thread": False} if database_url.startswith("sqlite") else {}


engine = create_engine(get_settings().database_url, connect_args=_connect_args(get_settings().database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.database import models  # noqa: F401
    from app.database.seed import seed_requirements

    Base.metadata.create_all(bind=engine)
    _apply_lightweight_sqlite_migrations()
    db = SessionLocal()
    try:
        seed_requirements(db)
    finally:
        db.close()


def _apply_lightweight_sqlite_migrations() -> None:
    if not get_settings().database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "evidence_items" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("evidence_items")}
    migrations = {
        "due_date": "ALTER TABLE evidence_items ADD COLUMN due_date DATETIME",
        "expires_at": "ALTER TABLE evidence_items ADD COLUMN expires_at DATETIME",
        "approved_by": "ALTER TABLE evidence_items ADD COLUMN approved_by VARCHAR(255)",
        "approved_at": "ALTER TABLE evidence_items ADD COLUMN approved_at DATETIME",
        "review_notes": "ALTER TABLE evidence_items ADD COLUMN review_notes TEXT",
    }
    with engine.begin() as connection:
        for column, statement in migrations.items():
            if column not in existing:
                connection.execute(text(statement))
        table_columns = {
            table_name: {column["name"] for column in inspector.get_columns(table_name)}
            for table_name in ["ai_systems", "ai_system_profiles", "risk_assessments", "audit_events"]
            if table_name in inspector.get_table_names()
        }
        tenant_migrations = {
            "ai_systems": "ALTER TABLE ai_systems ADD COLUMN tenant_id VARCHAR(120) DEFAULT 'default'",
            "ai_system_profiles": "ALTER TABLE ai_system_profiles ADD COLUMN tenant_id VARCHAR(120) DEFAULT 'default'",
            "risk_assessments": "ALTER TABLE risk_assessments ADD COLUMN tenant_id VARCHAR(120) DEFAULT 'default'",
            "audit_events": "ALTER TABLE audit_events ADD COLUMN tenant_id VARCHAR(120) DEFAULT 'default'",
        }
        for table_name, statement in tenant_migrations.items():
            if table_name in table_columns and "tenant_id" not in table_columns[table_name]:
                connection.execute(text(statement))
