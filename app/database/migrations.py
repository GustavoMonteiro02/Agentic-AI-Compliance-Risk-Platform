from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Engine, inspect, text


@dataclass(frozen=True)
class ColumnMigration:
    table_name: str
    column_name: str
    ddl: str


@dataclass(frozen=True)
class DatabaseMigration:
    migration_id: str
    description: str
    operations: tuple[ColumnMigration, ...]


MIGRATIONS: tuple[DatabaseMigration, ...] = (
    DatabaseMigration(
        migration_id="20260610_001_evidence_lifecycle",
        description="Add evidence lifecycle due date, expiry, approval, and review note fields.",
        operations=(
            ColumnMigration("evidence_items", "due_date", "ALTER TABLE evidence_items ADD COLUMN due_date DATETIME"),
            ColumnMigration("evidence_items", "expires_at", "ALTER TABLE evidence_items ADD COLUMN expires_at DATETIME"),
            ColumnMigration(
                "evidence_items",
                "approved_by",
                "ALTER TABLE evidence_items ADD COLUMN approved_by VARCHAR(255)",
            ),
            ColumnMigration("evidence_items", "approved_at", "ALTER TABLE evidence_items ADD COLUMN approved_at DATETIME"),
            ColumnMigration("evidence_items", "review_notes", "ALTER TABLE evidence_items ADD COLUMN review_notes TEXT"),
        ),
    ),
    DatabaseMigration(
        migration_id="20260610_002_tenant_scoping",
        description="Add tenant scoping to core system, profile, assessment, and audit event tables.",
        operations=(
            ColumnMigration(
                "ai_systems",
                "tenant_id",
                "ALTER TABLE ai_systems ADD COLUMN tenant_id VARCHAR(120) DEFAULT 'default'",
            ),
            ColumnMigration(
                "ai_system_profiles",
                "tenant_id",
                "ALTER TABLE ai_system_profiles ADD COLUMN tenant_id VARCHAR(120) DEFAULT 'default'",
            ),
            ColumnMigration(
                "risk_assessments",
                "tenant_id",
                "ALTER TABLE risk_assessments ADD COLUMN tenant_id VARCHAR(120) DEFAULT 'default'",
            ),
            ColumnMigration(
                "audit_events",
                "tenant_id",
                "ALTER TABLE audit_events ADD COLUMN tenant_id VARCHAR(120) DEFAULT 'default'",
            ),
        ),
    ),
)


def apply_database_migrations(engine: Engine) -> dict:
    _ensure_schema_migrations_table(engine)
    applied = _applied_migrations(engine)
    applied_now: list[str] = []
    skipped: list[str] = []

    with engine.begin() as connection:
        inspector = inspect(connection)
        table_names = set(inspector.get_table_names())
        for migration in MIGRATIONS:
            if migration.migration_id in applied:
                skipped.append(migration.migration_id)
                continue

            for operation in migration.operations:
                if operation.table_name not in table_names:
                    continue
                columns = {column["name"] for column in inspector.get_columns(operation.table_name)}
                if operation.column_name not in columns:
                    connection.execute(text(operation.ddl))

            connection.execute(
                text(
                    "INSERT INTO schema_migrations (migration_id, description, applied_at) "
                    "VALUES (:migration_id, :description, :applied_at)"
                ),
                {
                    "migration_id": migration.migration_id,
                    "description": migration.description,
                    "applied_at": datetime.now(UTC).isoformat(),
                },
            )
            applied_now.append(migration.migration_id)

    return {**migration_status(engine), "applied_now": applied_now, "skipped": skipped}


def migration_status(engine: Engine) -> dict:
    _ensure_schema_migrations_table(engine)
    applied = _applied_migrations(engine)
    migration_ids = [migration.migration_id for migration in MIGRATIONS]
    pending = [migration_id for migration_id in migration_ids if migration_id not in applied]
    return {
        "ok": not pending,
        "current": not pending,
        "applied": [migration_id for migration_id in migration_ids if migration_id in applied],
        "pending": pending,
        "available": migration_ids,
    }


def _ensure_schema_migrations_table(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "migration_id VARCHAR(255) PRIMARY KEY, "
                "description TEXT NOT NULL, "
                "applied_at VARCHAR(80) NOT NULL"
                ")"
            )
        )


def _applied_migrations(engine: Engine) -> set[str]:
    with engine.begin() as connection:
        rows = connection.execute(text("SELECT migration_id FROM schema_migrations")).fetchall()
    return {row[0] for row in rows}
