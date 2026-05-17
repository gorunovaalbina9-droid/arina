from pathlib import Path

import pytest

from center_voice_agent.modes.commands import ModeCommandsFile, ModeCommandEntry, try_parse_mode_switch


def test_try_parse_phrase() -> None:
    cmds = ModeCommandsFile(
        entries=[ModeCommandEntry(mode_id="lesson", phrases=["переключись в учебный"])]
    )
    aliases = {"dialog": ["поболтаем"]}
    assert try_parse_mode_switch("  переключись в учебный  ", commands=cmds, voice_aliases=aliases) == "lesson"
    assert try_parse_mode_switch("давай поболтаем", commands=cmds, voice_aliases=aliases) == "dialog"


@pytest.mark.asyncio
async def test_coordinator_switches_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "sess.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)

    from center_voice_agent.agent.fake_llm import StaticChatModel
    from center_voice_agent.agent.gateway import AgentGateway
    from center_voice_agent.db.session import init_database
    from center_voice_agent.orchestration.coordinator import SessionCoordinator
    from center_voice_agent.context.short_term import ShortTermMemory
    from center_voice_agent.settings import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    project_root = Path(__file__).resolve().parents[1]
    await init_database(project_root, settings.database_url)

    llm = StaticChatModel(responses=["ок"])
    gw = AgentGateway(settings=settings, llm=llm)
    coord = SessionCoordinator(gw, settings=settings)
    stm = ShortTermMemory(max_turns=15)

    r1 = await coord.handle_user_turn(
        session_id="s-coord-1",
        child_profile_id="child-1",
        user_text="переключись в учебный",
        short_term=stm,
        age_band="5-6",
    )
    assert r1.mode_changed is True
    assert r1.mode_id == "lesson"

    r2 = await coord.handle_user_turn(
        session_id="s-coord-1",
        child_profile_id="child-1",
        user_text="ещё раз привет",
        short_term=stm,
        age_band="5-6",
    )
    assert r2.mode_changed is False
    assert r2.mode_id == "lesson"

    await gw.aclose()
