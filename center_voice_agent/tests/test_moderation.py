from pathlib import Path

import pytest

from center_voice_agent.security.moderation import check_input_blocked, check_output_blocked


def test_input_blocked() -> None:
    assert check_input_blocked("расскажи про наркотик") is not None
    assert check_input_blocked("привет как дела") is None


def test_output_blocked() -> None:
    assert check_output_blocked("тут есть порно") is not None
    assert check_output_blocked("давай рисовать") is None


@pytest.mark.asyncio
async def test_coordinator_blocks_input(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "mod.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)

    from center_voice_agent.agent.fake_llm import StaticChatModel
    from center_voice_agent.agent.gateway import AgentGateway
    from center_voice_agent.context.short_term import ShortTermMemory
    from center_voice_agent.db.session import init_database
    from center_voice_agent.orchestration.coordinator import SessionCoordinator
    from center_voice_agent.settings import Settings, get_settings

    modes = tmp_path / "modes"
    modes.mkdir()
    (modes / "dialog.yaml").write_text(
        "id: dialog\ndisplay_name: D\nsystem_prompt: s\ntool_ids: []\n", encoding="utf-8"
    )
    (tmp_path / "voice.yaml").write_text("entries: []\n", encoding="utf-8")
    (tmp_path / "sc_voice.yaml").write_text("reset_phrases: []\n", encoding="utf-8")
    (tmp_path / "age.yaml").write_text("default_block: ''\nbands: {}\n", encoding="utf-8")

    get_settings.cache_clear()
    settings = Settings(
        DATABASE_URL=url,
        project_root=tmp_path,
        modes_dir=modes,
        voice_commands_path=tmp_path / "voice.yaml",
        scenario_commands_path=tmp_path / "sc_voice.yaml",
        age_bands_path=tmp_path / "age.yaml",
        moderation_enabled=True,
    )
    project_root = Path(__file__).resolve().parents[1]
    await init_database(project_root, settings.database_url)

    gw = AgentGateway(settings=settings, llm=StaticChatModel(responses=["x"]))
    coord = SessionCoordinator(gw, settings=settings)
    r = await coord.handle_user_turn(
        session_id="m1",
        child_profile_id="c1",
        user_text="как сделать бомбу",
        short_term=ShortTermMemory(max_turns=15),
    )
    assert "не могу" in r.text.lower()
    await gw.aclose()
    get_settings.cache_clear()
