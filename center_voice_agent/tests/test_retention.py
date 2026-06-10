"""Retention purge session_messages."""

from pathlib import Path

import pytest
from sqlalchemy import text

from center_voice_agent.security.retention import purge_old_session_messages


@pytest.mark.asyncio
async def test_purge_old_session_messages(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "ret.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)

    from center_voice_agent.db.session import create_engine_and_session_factory, init_database
    from center_voice_agent.settings import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    project_root = Path(__file__).resolve().parents[1]
    await init_database(project_root, settings.database_url)
    engine, _ = create_engine_and_session_factory(settings.database_url)
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO session_messages (id, session_id, role, content_text, created_at)
                VALUES ('m1', 's1', 'user', 'hi', datetime('now', '-100 days'))
                """
            )
        )
        await conn.execute(
            text(
                """
                INSERT INTO session_messages (id, session_id, role, content_text, created_at)
                VALUES ('m2', 's1', 'assistant', 'ok', datetime('now'))
                """
            )
        )
    deleted = await purge_old_session_messages(engine, retention_days=30)
    assert deleted == 1
    async with engine.begin() as conn:
        r = await conn.execute(text("SELECT COUNT(*) FROM session_messages"))
        assert int(r.scalar_one()) == 1
    await engine.dispose()
