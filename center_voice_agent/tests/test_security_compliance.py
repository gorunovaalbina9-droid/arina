"""Тесты усиленной модерации, redact, web_search, consent."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from center_voice_agent.security.moderation_engine import (
    ModerationEngine,
    normalize_for_moderation,
)
from center_voice_agent.security.redact import redact_tool_call, redact_tool_calls
from center_voice_agent.tools.factory import build_tools_for_mode


def test_normalize_collapses_spaces() -> None:
    norm = normalize_for_moderation("как   сделать   бомбу")
    assert "как сделать бомбу" in norm


def test_regex_catches_rephrase() -> None:
    engine = ModerationEngine(
        blocked_input=(),
        blocked_output=(),
        input_patterns=(re.compile(r"как\s+сделать\s+бомб", re.IGNORECASE),),
        output_patterns=(),
    )
    assert engine.check_input("как   сделать   бомбу") is not None


def test_redact_memory_tool_args() -> None:
    call = {
        "name": "memory_upsert",
        "args": {"category": "interest", "value_text": "любит кошек", "child_profile_id": "c1"},
        "id": "1",
    }
    red = redact_tool_call(call)
    assert "любит" not in str(red["args"]["value_text"])
    assert "fp=" in str(red["args"]["value_text"])
    assert red["args"]["child_profile_id"] == "c1"


def test_redact_tool_calls_list() -> None:
    calls = [{"name": "memory_search", "args": {"query": "секрет"}, "id": "x"}]
    out = redact_tool_calls(calls)
    assert "секрет" not in str(out[0]["args"]["query"])


def test_web_search_stripped_when_disabled() -> None:
    tools = build_tools_for_mode(
        ["web_search"],
        memory_repo=None,
        child_profile_id="c1",
        web_search_enabled=False,
        mode_id="dialog",
    )
    assert len(tools) == 0


def test_web_search_allowed_only_in_listed_modes() -> None:
    tools = build_tools_for_mode(
        ["web_search"],
        memory_repo=None,
        child_profile_id="c1",
        web_search_enabled=True,
        mode_id="dialog",
        web_search_allowed_mode_ids=("staff",),
    )
    assert len(tools) == 0


@pytest.mark.asyncio
async def test_consent_blocks_turn(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "consent.db"
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
        require_parent_consent=True,
        moderation_enabled=False,
        rate_limit_enabled=False,
    )
    project_root = Path(__file__).resolve().parents[1]
    await init_database(project_root, settings.database_url)

    gw = AgentGateway(settings=settings, llm=StaticChatModel(responses=["ok"]))
    coord = SessionCoordinator(gw, settings=settings)
    r = await coord.handle_user_turn(
        session_id="c-sess",
        child_profile_id="child-no-consent",
        user_text="привет",
        short_term=ShortTermMemory(max_turns=15),
    )
    assert "согласие" in r.text.lower()
    await gw.aclose()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_consent_allows_with_meta_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "consent2.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)

    from center_voice_agent.agent.fake_llm import StaticChatModel
    from center_voice_agent.agent.gateway import AgentGateway
    from center_voice_agent.context.short_term import ShortTermMemory
    from center_voice_agent.db.session import init_database
    from center_voice_agent.orchestration.coordinator import SessionCoordinator
    from center_voice_agent.settings import Settings, get_settings
    from sqlalchemy import text

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
        require_parent_consent=True,
        moderation_enabled=False,
        rate_limit_enabled=False,
    )
    project_root = Path(__file__).resolve().parents[1]
    await init_database(project_root, settings.database_url)

    gw = AgentGateway(settings=settings, llm=StaticChatModel(responses=["привет!"]))
    await gw.memory_repository.ensure_child_profile("child-ok")
    async with gw.memory_repository._session_factory() as session:
        await session.execute(
            text("UPDATE child_profiles SET meta_json = :mj WHERE id = :id"),
            {"id": "child-ok", "mj": json.dumps({"parent_consent_at": "2026-01-01T00:00:00Z"})},
        )
        await session.commit()

    coord = SessionCoordinator(gw, settings=settings)
    r = await coord.handle_user_turn(
        session_id="c-sess2",
        child_profile_id="child-ok",
        user_text="привет",
        short_term=ShortTermMemory(max_turns=15),
    )
    assert "согласие" not in r.text.lower()
    await gw.aclose()
    get_settings.cache_clear()
