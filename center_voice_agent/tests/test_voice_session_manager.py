from pathlib import Path

import pytest

from center_voice_agent.composition.runtime import shutdown_process_container
from center_voice_agent.db.session import init_database
from center_voice_agent.settings import Settings, get_settings
from center_voice_agent.voice.session_manager import VoiceSessionManager


@pytest.mark.asyncio
async def test_voice_manager_reuses_session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "voice.db"
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
    await init_database(settings.project_root, settings.database_url)

    mgr = VoiceSessionManager()
    t1 = await mgr.ask(
        "привет",
        session_id="voice-room",
        child_profile_id="child-v",
        offline_llm=True,
    )
    t2 = await mgr.ask(
        "ещё",
        session_id="voice-room",
        child_profile_id="child-v",
        offline_llm=True,
    )
    assert "voice-room" in mgr._sessions
    assert t1
    assert t2
    await mgr.close_all()
    await shutdown_process_container()
    get_settings.cache_clear()
