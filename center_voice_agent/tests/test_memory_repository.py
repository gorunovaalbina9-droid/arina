from pathlib import Path

import pytest

from center_voice_agent.db.session import create_engine_and_session_factory, run_migrations
from center_voice_agent.memory.repository import LongTermMemoryRepository


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_memory_upsert_and_search(tmp_path: Path) -> None:
    dbfile = tmp_path / "test.db"
    url = f"sqlite+aiosqlite:///{dbfile.as_posix().replace(chr(92), '/')}"
    engine, session_factory = create_engine_and_session_factory(url)
    await run_migrations(engine, PROJECT_ROOT)
    repo = LongTermMemoryRepository(session_factory)

    out = await repo.upsert("child-1", "hobby", "любит рисовать", key="art")
    assert "добавлена" in out.lower()

    found = await repo.search("child-1", "рис", limit=5)
    assert "рис" in found.lower() or "рисов" in found.lower()

    out2 = await repo.upsert("child-1", "hobby", "любит акварель", key="art")
    assert "обновлена" in out2.lower()

    bad = await repo.upsert("child-1", "illegal_cat", "x")
    assert "не разрешена" in bad.lower()

    await engine.dispose()


@pytest.mark.asyncio
async def test_memory_search_like_escape(tmp_path: Path) -> None:
    dbfile = tmp_path / "like.db"
    url = f"sqlite+aiosqlite:///{dbfile.as_posix().replace(chr(92), '/')}"
    engine, session_factory = create_engine_and_session_factory(url)
    await run_migrations(engine, PROJECT_ROOT)
    repo = LongTermMemoryRepository(session_factory)

    await repo.upsert("child-like", "note", "готов на 100%")
    await repo.upsert("child-like", "hobby", "любит _подчёркивание")

    found_pct = await repo.search("child-like", "100%", limit=5)
    assert "100%" in found_pct

    found_us = await repo.search("child-like", "_под", limit=5)
    assert "подчёркивание" in found_us

    await engine.dispose()


def test_build_tools_requires_memory_when_mode_has_memory() -> None:
    from center_voice_agent.tools.factory import build_tools_for_mode

    with pytest.raises(ValueError):
        build_tools_for_mode(["memory_search"], memory_repo=None, child_profile_id="c1")

    assert build_tools_for_mode(
        ["web_search"],
        memory_repo=None,
        child_profile_id="c1",
        web_search_enabled=True,
    )
