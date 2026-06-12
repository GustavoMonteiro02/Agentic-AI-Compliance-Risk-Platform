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
    DatabaseMigration(
        migration_id="20260612_003_evidence_metadata",
        description="Add source, checksum, collection, retention, and metadata fields to evidence records.",
        operations=(
            ColumnMigration(
                "evidence_items",
                "source_system",
                "ALTER TABLE evidence_items ADD COLUMN source_system VARCHAR(255)",
            ),
            ColumnMigration(
                "evidence_items",
                "evidence_hash",
                "ALTER TABLE evidence_items ADD COLUMN evidence_hash VARCHAR(255)",
            ),
            ColumnMigration(
                "evidence_items",
                "collected_at",
                "ALTER TABLE evidence_items ADD COLUMN collected_at DATETIME",
            ),
            ColumnMigration(
                "evidence_items",
                "retention_until",
                "ALTER TABLE evidence_items ADD COLUMN retention_until DATETIME",
            ),
            ColumnMigration(
                "evidence_items",
                "evidence_metadata_json",
                "ALTER TABLE evidence_items ADD COLUMN evidence_metadata_json JSON DEFAULT '{}'",
            ),
        ),
    ),
)

TABLE_MIGRATIONS: tuple[tuple[str, str, str], ...] = (
    (
        "20260612_004_notification_outbox",
        "Create notification outbox table for review escalation and operational notifications.",
        "CREATE TABLE IF NOT EXISTS notification_events ("
        "id VARCHAR PRIMARY KEY, "
        "tenant_id VARCHAR(120) DEFAULT 'default', "
        "assessment_id VARCHAR, "
        "event_type VARCHAR(120), "
        "channel VARCHAR(80) DEFAULT 'in_app', "
        "recipient VARCHAR(255), "
        "subject VARCHAR(255), "
        "message TEXT, "
        "status VARCHAR(80) DEFAULT 'queued', "
        "dedupe_key VARCHAR(255), "
        "payload_json JSON DEFAULT '{}', "
        "created_at DATETIME, "
        "delivered_at DATETIME"
        ")",
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
        for migration_id, description, ddl in TABLE_MIGRATIONS:
            if migration_id in applied:
                skipped.append(migration_id)
                continue
            connection.execute(text(ddl))
            connection.execute(
                text(
                    "INSERT INTO schema_migrations (migration_id, description, applied_at) "
                    "VALUES (:migration_id, :description, :applied_at)"
                ),
                {
                    "migration_id": migration_id,
                    "description": description,
                    "applied_at": datetime.now(UTC).isoformat(),
                },
            )
            applied_now.append(migration_id)
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
    migration_ids = [migration.migration_id for migration in MIGRATIONS] + [
        migration_id for migration_id, _, _ in TABLE_MIGRATIONS
    ]
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
