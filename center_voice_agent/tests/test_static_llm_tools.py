"""E2E: StaticChatModel с нативными tool_calls через LangGraph."""

from __future__ import annotations

from pathlib import Path

import pytest

from center_voice_agent.agent.fake_llm import StaticChatModel
from center_voice_agent.agent.gateway import AgentGateway
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.db.session import create_engine_and_session_factory, run_migrations
from center_voice_agent.memory.repository import LongTermMemoryRepository
from center_voice_agent.settings import Settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_static_llm_native_tool_call_e2e(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "tools.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)

    modes = tmp_path / "modes"
    modes.mkdir()
    (modes / "dialog.yaml").write_text(
        "id: dialog\ndisplay_name: D\nsystem_prompt: s\ntool_ids:\n  - memory_upsert\n",
        encoding="utf-8",
    )
    (tmp_path / "voice.yaml").write_text("entries: []\n", encoding="utf-8")
    (tmp_path / "sc_voice.yaml").write_text("reset_phrases: []\n", encoding="utf-8")
    (tmp_path / "age.yaml").write_text("default_block: ''\nbands: {}\n", encoding="utf-8")

    settings = Settings(
        DATABASE_URL=url,
        project_root=tmp_path,
        modes_dir=modes,
        voice_commands_path=tmp_path / "voice.yaml",
        scenario_commands_path=tmp_path / "sc_voice.yaml",
        age_bands_path=tmp_path / "age.yaml",
        use_langgraph=True,
        text_tool_fallback=False,
    )
    engine, session_factory = create_engine_and_session_factory(url)
    await run_migrations(engine, PROJECT_ROOT)
    memory = LongTermMemoryRepository(session_factory)

    llm = StaticChatModel.with_tool_then_text(
        tool_name="memory_upsert",
        tool_args={"category": "hobby", "value_text": "любит роботов"},
        text="Запомнила, ты любишь роботов!",
    )
    gw = AgentGateway(settings=settings, llm=llm, memory_repository=memory)
    stm = ShortTermMemory(max_turns=15)
    r = await gw.run_turn(
        session_id="tool-e2e",
        child_profile_id="child-tools",
        mode_id="dialog",
        user_text="запомни что я люблю роботов",
        short_term=stm,
    )
    assert r.tool_calls
    assert r.tool_calls[0]["name"] == "memory_upsert"
    assert "робот" in r.text.lower()
    found = await memory.search("child-tools", "робот", limit=3)
    assert "робот" in found.lower()
    await gw.aclose()
    await engine.dispose()


@pytest.mark.asyncio
async def test_langgraph_compiles_fresh_each_invoke() -> None:
    from center_voice_agent.agent.turn_langgraph import compile_llm_tool_graph

    g1 = compile_llm_tool_graph()
    g2 = compile_llm_tool_graph()
    assert g1 is not g2
