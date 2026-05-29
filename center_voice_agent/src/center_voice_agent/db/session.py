from __future__ import annotations

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine


def _migration_dir(project_root: Path) -> Path:
    return project_root / "db" / "migrations"


def _migration_files(project_root: Path) -> list[Path]:
    d = _migration_dir(project_root)
    if not d.is_dir():
        return []
    return sorted(d.glob("*.sql"), key=lambda p: p.name)


def _split_sql_statements(raw: str) -> list[str]:
    statements: list[str] = []
    for block in raw.split(";"):
        lines = [
            ln
            for ln in block.splitlines()
            if ln.strip() and not ln.strip().lstrip("\ufeff").startswith("--")
        ]
        stmt = "\n".join(lines).strip()
        if stmt:
            statements.append(stmt)
    return statements


async def _ensure_schema_migrations_table(conn) -> None:
    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
    )


_LEGACY_MIGRATION_VERSIONS = frozenset(
    {
        "001_init",
        "002_mode_definitions",
        "004_scenario_publish",
        "005_session_messages",
    }
)


async def _backfill_schema_migrations(conn, files: list[Path]) -> None:
    """БД создана до учёта версий: пометить старые миграции; 003/006 применятся отдельно."""
    r = await conn.execute(text("SELECT COUNT(*) FROM schema_migrations"))
    if int(r.scalar() or 0) > 0:
        return
    r2 = await conn.execute(
        text(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='session_state' LIMIT 1"
        )
    )
    if r2.fetchone() is None:
        return
    for sql_path in files:
        ver = sql_path.stem
        if ver not in _LEGACY_MIGRATION_VERSIONS:
            continue
        await conn.execute(
            text("INSERT OR IGNORE INTO schema_migrations (version) VALUES (:v)"),
            {"v": ver},
        )


async def run_migrations(engine: AsyncEngine, project_root: Path) -> None:
    files = _migration_files(project_root)
    if not files:
        raise FileNotFoundError(f"Нет SQL-миграций в {_migration_dir(project_root)}")
    async with engine.begin() as conn:
        await _ensure_schema_migrations_table(conn)
        await _backfill_schema_migrations(conn, files)
        for sql_path in files:
            version = sql_path.stem
            cur = await conn.execute(
                text("SELECT 1 FROM schema_migrations WHERE version = :v"),
                {"v": version},
            )
            if cur.fetchone() is not None:
                continue
            raw = sql_path.read_text(encoding="utf-8-sig")
            for stmt in _split_sql_statements(raw):
                await conn.execute(text(stmt))
            await conn.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:v)"),
                {"v": version},
            )


def create_engine_and_session_factory(database_url: str) -> tuple[AsyncEngine, async_sessionmaker]:
    engine = create_async_engine(database_url, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, factory


def ensure_sqlite_parent_dir(database_url: str) -> None:
    """Создать родительский каталог для файла SQLite."""
    prefixes = ("sqlite+aiosqlite:///", "sqlite:///")
    path_part: str | None = None
    for prefix in prefixes:
        if database_url.startswith(prefix):
            path_part = database_url[len(prefix) :]
            break
    if path_part is None:
        return
    path_part = path_part.replace("\\", "/")
    p = Path(path_part)
    if p.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
        p.parent.mkdir(parents=True, exist_ok=True)


async def init_database(project_root: Path, database_url: str) -> None:
    """Создать каталог БД и применить миграции (идемпотентно)."""
    ensure_sqlite_parent_dir(database_url)
    engine, _ = create_engine_and_session_factory(database_url)
    try:
        await run_migrations(engine, project_root)
    finally:
        await engine.dispose()
