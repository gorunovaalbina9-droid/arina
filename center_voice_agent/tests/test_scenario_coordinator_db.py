"""6.5.3: coordinator + check_in_three, узлы после ходов."""

from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_coordinator_advances_check_in_three(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "sc.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)

    from center_voice_agent.agent.fake_llm import StaticChatModel
    from center_voice_agent.agent.gateway import AgentGateway
    from center_voice_agent.context.short_term import ShortTermMemory
    from center_voice_agent.db.session import init_database
    from center_voice_agent.orchestration.coordinator import SessionCoordinator
    from center_voice_agent.settings import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    project_root = Path(__file__).resolve().parents[1]
    await init_database(project_root, settings.database_url)

    gw = AgentGateway(settings=settings, llm=StaticChatModel(responses=["ok", "ok", "ok"]))
    coord = SessionCoordinator(gw, settings=settings)
    stm = ShortTermMemory(max_turns=15)
    sid = "sc-demo"

    await gw.session_repository.ensure(sid, "child-1", default_mode_id="dialog")
    await gw.session_repository.attach_scenario(sid, "check_in_three")

    r1 = await coord.handle_user_turn(
        session_id=sid, child_profile_id="child-1", user_text="Привет", short_term=stm
    )
    assert r1.scenario_node_id == "reflect"

    r2 = await coord.handle_user_turn(
        session_id=sid, child_profile_id="child-1", user_text="Нормально", short_term=stm
    )
    assert r2.scenario_node_id == "close"

    await gw.aclose()
    get_settings.cache_clear()
