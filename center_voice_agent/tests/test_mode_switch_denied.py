"""Отказ смены режима: фраза распознана, но цель не в allowed_transitions."""

from __future__ import annotations

from pathlib import Path

import pytest

from center_voice_agent.agent.fake_llm import StaticChatModel
from center_voice_agent.agent.gateway import AgentGateway
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.db.session import init_database
from center_voice_agent.orchestration.coordinator import SessionCoordinator
from center_voice_agent.settings import Settings, get_settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_mode_switch_denied_when_transition_not_allowed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "deny.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("DEFAULT_MODE_ID", "narrow")
    get_settings.cache_clear()

    modes = tmp_path / "modes"
    modes.mkdir()
    (modes / "narrow.yaml").write_text(
        "id: narrow\ndisplay_name: N\nsystem_prompt: sn\n"
        "allowed_transitions:\n  - mid\ntool_ids: []\n",
        encoding="utf-8",
    )
    (modes / "mid.yaml").write_text(
        "id: mid\ndisplay_name: M\nsystem_prompt: sm\ntool_ids: []\n", encoding="utf-8"
    )
    (modes / "wide.yaml").write_text(
        "id: wide\ndisplay_name: W\nsystem_prompt: sw\ntool_ids: []\n", encoding="utf-8"
    )
    (tmp_path / "voice.yaml").write_text(
        'entries:\n  - mode_id: wide\n    phrases: ["режим wide"]\n',
        encoding="utf-8",
    )
    (tmp_path / "age.yaml").write_text("default_block: ''\nbands: {}\n", encoding="utf-8")

    settings = Settings(
        DATABASE_URL=url,
        project_root=tmp_path,
        modes_dir=modes,
        voice_commands_path=tmp_path / "voice.yaml",
        age_bands_path=tmp_path / "age.yaml",
    )
    assert settings.default_mode_id == "narrow"
    await init_database(PROJECT_ROOT, settings.database_url)

    gw = AgentGateway(settings=settings, llm=StaticChatModel(responses=["продолжаем в текущем режиме."]))
    coord = SessionCoordinator(gw, settings=settings)
    stm = ShortTermMemory(max_turns=15)

    r = await coord.handle_user_turn(
        session_id="sess-deny-1",
        child_profile_id="child-x",
        user_text="режим wide",
        short_term=stm,
    )
    assert r.mode_changed is False
    assert r.mode_id == "narrow"
    assert "продолжаем" in r.text.lower() or len(r.text) > 0

    row = await gw.session_repository.get("sess-deny-1")
    assert row is not None and row.mode_id == "narrow"

    await gw.aclose()
    monkeypatch.delenv("DEFAULT_MODE_ID", raising=False)
    get_settings.cache_clear()
