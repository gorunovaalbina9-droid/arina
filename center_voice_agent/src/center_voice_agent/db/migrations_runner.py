"""Применение версионированных SQL-миграций (schema_migrations + диалект)."""

from __future__ import annotations

from pathlib import Path

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from center_voice_agent.db.dialect import (
    DbDialect,
    detect_dialect,
    insert_migration_ignore_sql,
    schema_migrations_ddl,
    table_exists,
)

log = structlog.get_logger(__name__)

_LEGACY_MIGRATION_VERSIONS = frozenset(
    {
        "001_init",
        "002_mode_definitions",
        "003_schema_migrations",
        "004_scenario_publish",
        "005_session_messages",
    }
)


def migration_dir(project_root: Path, dialect: DbDialect) -> Path:
    root = project_root / "db" / "migrations"
    sub = root / dialect
    if sub.is_dir():
        return sub
    return root


def migration_files(project_root: Path, dialect: DbDialect) -> list[Path]:
    d = migration_dir(project_root, dialect)
    if not d.is_dir():
        raise FileNotFoundError(f"Нет каталога миграций: {d}")
    files = sorted(d.glob("*.sql"), key=lambda p: p.name)
    if not files:
        raise FileNotFoundError(f"Нет SQL-файлов в {d}")
    return files


def split_sql_statements(raw: str) -> list[str]:
    """
    Разбор SQL без наивного split(';'): учитывает строки и line-comments.
    Подходит для DDL без dollar-quoting в теле функций.
    """
    statements: list[str] = []
    buf: list[str] = []
    in_single = False
    in_double = False
    i = 0
    n = len(raw)

    while i < n:
        ch = raw[i]

        if not in_single and not in_double and ch == "-" and i + 1 < n and raw[i + 1] == "-":
            while i < n and raw[i] != "\n":
                i += 1
            continue

        if in_single:
            buf.append(ch)
            if ch == "'":
                if i + 1 < n and raw[i + 1] == "'":
                    buf.append(raw[i + 1])
                    i += 2
                    continue
                in_single = False
            i += 1
            continue

        if in_double:
            buf.append(ch)
            if ch == '"':
                if i + 1 < n and raw[i + 1] == '"':
                    buf.append(raw[i + 1])
                    i += 2
                    continue
                in_double = False
            i += 1
            continue

        if ch == "'":
            in_single = True
            buf.append(ch)
            i += 1
            continue
        if ch == '"':
            in_double = True
            buf.append(ch)
            i += 1
            continue
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


async def _ensure_schema_migrations_table(conn, dialect: DbDialect) -> None:
    await conn.execute(text(schema_migrations_ddl(dialect)))


async def _backfill_schema_migrations(
    conn,
    files: list[Path],
    *,
    dialect: DbDialect,
) -> None:
    """БД до schema_migrations: пометить уже существующие таблицы как применённые."""
    cur = await conn.execute(text("SELECT COUNT(*) FROM schema_migrations"))
    if int(cur.scalar() or 0) > 0:
        return
    if not await table_exists(conn, dialect, "session_state"):
        return
    sql = insert_migration_ignore_sql(dialect)
    for sql_path in files:
        ver = sql_path.stem
        if ver not in _LEGACY_MIGRATION_VERSIONS:
            continue
        await conn.execute(text(sql), {"v": ver})


async def run_migrations(engine: AsyncEngine, project_root: Path) -> None:
    dialect = detect_dialect(str(engine.url))
    files = migration_files(project_root, dialect)
    log.info("migrations_start", dialect=dialect, count=len(files))
    async with engine.begin() as conn:
        await _ensure_schema_migrations_table(conn, dialect)
        await _backfill_schema_migrations(conn, files, dialect=dialect)
        for sql_path in files:
            version = sql_path.stem
            cur = await conn.execute(
                text("SELECT 1 FROM schema_migrations WHERE version = :v"),
                {"v": version},
            )
            if cur.fetchone() is not None:
                continue
            raw = sql_path.read_text(encoding="utf-8-sig")
            for stmt in split_sql_statements(raw):
                await conn.execute(text(stmt))
            await conn.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:v)"),
                {"v": version},
            )
            log.info("migration_applied", version=version, dialect=dialect)
