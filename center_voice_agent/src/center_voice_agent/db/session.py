from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from center_voice_agent.db.migrations_runner import run_migrations


def _migration_dir(project_root: Path) -> Path:
    return project_root / "db" / "migrations"


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
