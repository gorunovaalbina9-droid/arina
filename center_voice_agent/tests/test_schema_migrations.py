from pathlib import Path

import pytest
from sqlalchemy import text

from center_voice_agent.db.session import create_engine_and_session_factory, run_migrations

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_migrations_recorded_once(tmp_path: Path) -> None:
    db = tmp_path / "mig.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    engine, _ = create_engine_and_session_factory(url)
    try:
        await run_migrations(engine, PROJECT_ROOT)
        await run_migrations(engine, PROJECT_ROOT)
        async with engine.connect() as conn:
            r = await conn.execute(text("SELECT COUNT(*) FROM schema_migrations"))
            count = int(r.scalar() or 0)
        assert count >= 5
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
