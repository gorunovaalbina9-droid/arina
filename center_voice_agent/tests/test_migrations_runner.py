from pathlib import Path

import pytest

from center_voice_agent.db.dialect import detect_dialect
from center_voice_agent.db.migrations_runner import migration_files, split_sql_statements
from center_voice_agent.db.session import create_engine_and_session_factory, run_migrations

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_split_sql_respects_string_semicolon() -> None:
    raw = "INSERT INTO t (x) VALUES ('a;b');\nCREATE TABLE u (id INT);"
    parts = split_sql_statements(raw)
    assert len(parts) == 2
    assert "a;b" in parts[0]
    assert parts[1].startswith("CREATE")


def test_detect_dialect() -> None:
    assert detect_dialect("sqlite+aiosqlite:///./x.db") == "sqlite"
    assert detect_dialect("postgresql+asyncpg://u:p@localhost/db") == "postgresql"


def test_migration_dirs_exist() -> None:
    sqlite_files = migration_files(PROJECT_ROOT, "sqlite")
    pg_files = migration_files(PROJECT_ROOT, "postgresql")
    assert len(sqlite_files) == len(pg_files) == 6
    assert any(p.name.startswith("003_") for p in sqlite_files)


@pytest.mark.asyncio
async def test_migrations_recorded_once(tmp_path: Path) -> None:
    from sqlalchemy import text

    db = tmp_path / "mig.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    engine, _ = create_engine_and_session_factory(url)
    try:
        await run_migrations(engine, PROJECT_ROOT)
        await run_migrations(engine, PROJECT_ROOT)
        async with engine.connect() as conn:
            r = await conn.execute(text("SELECT COUNT(*) FROM schema_migrations"))
            count = int(r.scalar() or 0)
        assert count == 6
        async with engine.connect() as conn:
            r2 = await conn.execute(
                text(
                    "SELECT 1 FROM sqlite_master WHERE type='table' "
                    "AND name='scenario_definitions_legacy'"
                )
            )
        assert r2.fetchone() is not None
    finally:
        await engine.dispose()
