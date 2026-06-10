"""Определение диалекта БД и SQL-хелперы для SQLite / PostgreSQL."""

from __future__ import annotations

from typing import Literal

DbDialect = Literal["sqlite", "postgresql"]


def detect_dialect(database_url: str) -> DbDialect:
    url = (database_url or "").lower()
    if url.startswith("postgresql") or url.startswith("postgres+"):
        return "postgresql"
    return "sqlite"


def now_sql(dialect: DbDialect) -> str:
    if dialect == "postgresql":
        return "CURRENT_TIMESTAMP"
    return "datetime('now')"


def insert_migration_ignore_sql(dialect: DbDialect) -> str:
    if dialect == "postgresql":
        return "INSERT INTO schema_migrations (version) VALUES (:v) ON CONFLICT (version) DO NOTHING"
    return "INSERT OR IGNORE INTO schema_migrations (version) VALUES (:v)"


def schema_migrations_ddl(dialect: DbDialect) -> str:
    ts = now_sql(dialect)
    if dialect == "postgresql":
        return f"""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT {ts}
            )
        """
    return f"""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT ({ts})
        )
    """


async def table_exists(conn, dialect: DbDialect, table_name: str) -> bool:
    from sqlalchemy import text

    if dialect == "postgresql":
        cur = await conn.execute(
            text(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = :t
                LIMIT 1
                """
            ),
            {"t": table_name},
        )
    else:
        cur = await conn.execute(
            text(
                """
                SELECT 1 FROM sqlite_master
                WHERE type='table' AND name=:t
                LIMIT 1
                """
            ),
            {"t": table_name},
        )
    return cur.fetchone() is not None
