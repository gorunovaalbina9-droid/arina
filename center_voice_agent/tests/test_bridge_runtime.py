from pathlib import Path

import pytest

from center_voice_agent.agent.fake_llm import StaticChatModel
from center_voice_agent.composition.runtime import (
    get_process_container,
    reset_process_runtime_for_tests,
    shutdown_process_container,
)
from center_voice_agent.db.session import init_database
from center_voice_agent.integration.bridge import AgentSession
from center_voice_agent.settings import Settings, get_settings


@pytest.mark.asyncio
async def test_process_container_reused(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "rt.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)

    get_settings.cache_clear()
    modes = tmp_path / "modes"
    modes.mkdir()
    (modes / "dialog.yaml").write_text(
        "id: dialog\ndisplay_name: D\nsystem_prompt: test\ntool_ids: []\n",
        encoding="utf-8",
    )
    settings = Settings(
        DATABASE_URL=url,
        project_root=Path(__file__).resolve().parents[1],
        modes_dir=modes,
    )
    reset_process_runtime_for_tests()
    await init_database(settings.project_root, settings.database_url)

    c1 = await get_process_container(settings)
    c2 = await get_process_container(settings)
    assert c1 is c2
    assert c1.engine is c2.engine

    session = await AgentSession.open_with_container(
        c1,
        session_id="reuse-1",
        child_profile_id="child-r",
        llm=StaticChatModel(responses=["ок"]),
    )
    result = await session.ask("привет")
    assert "ок" in session.spoken_text(result).lower()
    await session.close()
    await shutdown_process_container()
    get_settings.cache_clear()
