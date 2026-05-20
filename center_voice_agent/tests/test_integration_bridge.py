from pathlib import Path

import pytest

from center_voice_agent.agent.fake_llm import StaticChatModel
from center_voice_agent.agent.gateway import AgentGateway
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.db.session import init_database
from center_voice_agent.integration.bridge import AgentSession
from center_voice_agent.orchestration.coordinator import SessionCoordinator
from center_voice_agent.settings import Settings, get_settings


@pytest.mark.asyncio
async def test_agent_session_with_fake_llm(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "br.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)

    get_settings.cache_clear()
    modes = tmp_path / "modes"
    modes.mkdir()
    (modes / "dialog.yaml").write_text(
        "id: dialog\ndisplay_name: D\nsystem_prompt: test\ntool_ids: []\n", encoding="utf-8"
    )
    settings = Settings(
        DATABASE_URL=url,
        project_root=Path(__file__).resolve().parents[1],
        modes_dir=modes,
    )
    await init_database(settings.project_root, settings.database_url)

    gateway = AgentGateway(settings=settings, llm=StaticChatModel(responses=["ответ моста"]))
    coord = SessionCoordinator(gateway, settings=settings)
    stm = ShortTermMemory(max_turns=15)
    session = AgentSession(
        coordinator=coord,
        short_term=stm,
        session_id="bridge-test",
        child_profile_id="child-b",
        age_band="5-6",
    )

    result = await session.ask("привет")
    assert "ответ" in session.spoken_text(result).lower()
    await session.close()
    get_settings.cache_clear()
