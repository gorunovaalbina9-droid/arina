from pathlib import Path

import pytest

from center_voice_agent.agent.fake_llm import StaticChatModel
from center_voice_agent.composition.container import AppContainer
from center_voice_agent.context.short_term_factory import build_short_term_memory
from center_voice_agent.context.session_messages_repo import SessionMessagesRepository
from center_voice_agent.db.session import create_engine_and_session_factory, run_migrations
from center_voice_agent.settings import Settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_session_messages_append_trim_load(tmp_path: Path) -> None:
    dbfile = tmp_path / "stm.db"
    url = f"sqlite+aiosqlite:///{dbfile.as_posix().replace(chr(92), '/')}"
    engine, session_factory = create_engine_and_session_factory(url)
    await run_migrations(engine, PROJECT_ROOT)

    from center_voice_agent.session.repo import SessionStateRepository

    sessions = SessionStateRepository(session_factory)
    repo = SessionMessagesRepository(session_factory)
    await sessions.ensure("s1", "child-1", default_mode_id="dialog")

    for i in range(20):
        await repo.append("s1", "user", f"u{i}")
        await repo.append("s1", "assistant", f"a{i}")

    await repo.trim("s1", keep=15)
    loaded = await repo.load_recent("s1", limit=15)
    assert len(loaded) == 15
    assert loaded[-1] == ("assistant", "a19")

    await engine.dispose()


@pytest.mark.asyncio
async def test_short_term_db_survives_new_container(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dbfile = tmp_path / "persist.db"
    url = f"sqlite+aiosqlite:///{dbfile.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("SHORT_TERM_SOURCE", "db")

    settings = Settings(
        project_root=PROJECT_ROOT,
        database_url=url,
        short_term_source="db",
        short_term_max_messages=15,
        moderation_enabled=False,
        rate_limit_enabled=False,
    )
    engine, session_factory = create_engine_and_session_factory(url)
    await run_migrations(engine, PROJECT_ROOT)
    await engine.dispose()

    container_a = AppContainer.from_settings(settings)
    coord_a = container_a.build_coordinator(llm=StaticChatModel(reply="ответ один"))
    sid = "sess-restart-1"
    stm_a = await build_short_term_memory(
        sid, settings=settings, messages_repo=container_a.session_messages_repository
    )
    await coord_a.handle_user_turn(
        session_id=sid,
        child_profile_id="child-1",
        user_text="привет",
        short_term=stm_a,
    )
    await container_a.aclose()

    container_b = AppContainer.from_settings(settings)
    stm_b = await build_short_term_memory(
        sid, settings=settings, messages_repo=container_b.session_messages_repository
    )
    assert len(stm_b) == 2
    assert stm_b.snapshot()[0] == ("user", "привет")
    assert stm_b.snapshot()[1][0] == "assistant"
    await container_b.aclose()


@pytest.mark.asyncio
async def test_parent_progress_report_list(tmp_path: Path) -> None:
    dbfile = tmp_path / "prog.db"
    url = f"sqlite+aiosqlite:///{dbfile.as_posix().replace(chr(92), '/')}"
    engine, session_factory = create_engine_and_session_factory(url)
    await run_migrations(engine, PROJECT_ROOT)
    from center_voice_agent.memory.repository import LongTermMemoryRepository

    repo = LongTermMemoryRepository(session_factory)
    await repo.upsert("child-p", "progress", "прошёл урок про цвета", key="art")
    await repo.upsert("child-p", "note", "спокойный на занятии")
    rows = await repo.list_entries("child-p", "progress", limit=5)
    assert len(rows) == 1
    assert "цвет" in rows[0].value_text
    await engine.dispose()
