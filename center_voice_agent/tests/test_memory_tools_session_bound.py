from pathlib import Path

import pytest

from center_voice_agent.memory.repository import LongTermMemoryRepository
from center_voice_agent.settings import Settings
from center_voice_agent.tools.factory import build_tools_for_mode


@pytest.mark.asyncio
async def test_memory_tools_ignore_llm_child_id_override(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from center_voice_agent.db.session import create_engine_and_session_factory, run_migrations

    dbfile = tmp_path / "t.db"
    url = f"sqlite+aiosqlite:///{dbfile.as_posix().replace(chr(92), '/')}"
    engine, session_factory = create_engine_and_session_factory(url)
    import shutil

    project = tmp_path / "proj"
    real_root = Path(__file__).resolve().parents[1]
    shutil.copytree(real_root / "db" / "migrations", project / "db" / "migrations")
    (project / "config").mkdir(parents=True, exist_ok=True)
    await run_migrations(engine, project)
    repo = LongTermMemoryRepository(session_factory)

    tools = build_tools_for_mode(
        ["memory_upsert"],
        memory_repo=repo,
        child_profile_id="child-real",
    )
    upsert = tools[0]
    await upsert.ainvoke(
        {"category": "hobby", "value_text": "маркер session-bound", "child_profile_id": "child-hacker"}
    )
    found = await repo.search("child-real", "session-bound", limit=5)
    assert "session-bound" in found
    empty = await repo.search("child-hacker", "session-bound", limit=5)
    assert "session-bound" not in (empty or "")
    await engine.dispose()
