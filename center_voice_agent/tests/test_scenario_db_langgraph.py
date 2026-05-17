from pathlib import Path

import pytest

from center_voice_agent.scenarios.db_source import publish_scenario_yaml_sync
from center_voice_agent.scenarios.loader import clear_scenario_scan_cache, load_scenario_graph_unified


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_scenario_hybrid_loads_from_db(tmp_path: Path) -> None:
    from center_voice_agent.db.session import create_engine_and_session_factory, run_migrations

    dbfile = tmp_path / "sc.db"
    url = f"sqlite+aiosqlite:///{dbfile.as_posix().replace(chr(92), '/')}"
    engine, _ = create_engine_and_session_factory(url)
    await run_migrations(engine, PROJECT_ROOT)
    await engine.dispose()

    scen = tmp_path / "scenarios"
    scen.mkdir(parents=True)
    (scen / "file.yaml").write_text(
        "id: ov\nentry: a\nnodes:\n  a:\n    title: A\n    prompt_to_model: from file\n    transitions: []\n",
        encoding="utf-8",
    )
    yaml_db = """id: ov
entry: a
nodes:
  a:
    title: A
    prompt_to_model: from database
    transitions: []
"""
    publish_scenario_yaml_sync(url, config_yaml=yaml_db, scenario_id="ov", center_id=None, status="published")
    clear_scenario_scan_cache()

    g = load_scenario_graph_unified(
        scen,
        "ov",
        database_url=url,
        scenarios_source="hybrid",
        scenarios_center_id=None,
    )
    assert "database" in g.nodes["a"].prompt_to_model
    clear_scenario_scan_cache()


@pytest.mark.asyncio
async def test_gateway_langgraph_static_llm(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from center_voice_agent.agent.fake_llm import StaticChatModel
    from center_voice_agent.agent.gateway import AgentGateway
    from center_voice_agent.context.short_term import ShortTermMemory
    from center_voice_agent.db.session import init_database
    from center_voice_agent.settings import Settings, get_settings

    db = tmp_path / "g.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    modes = tmp_path / "modes"
    modes.mkdir()
    (modes / "dialog.yaml").write_text(
        "id: dialog\ndisplay_name: D\nsystem_prompt: You are brief.\ntool_ids: []\n", encoding="utf-8"
    )
    settings = Settings(
        DATABASE_URL=url,
        project_root=tmp_path,
        modes_dir=modes,
        use_langgraph=True,
    )
    await init_database(PROJECT_ROOT, settings.database_url)
    gw = AgentGateway(settings=settings, llm=StaticChatModel(responses=["ok"]))
    stm = ShortTermMemory(max_turns=15)
    r = await gw.run_turn(
        session_id="lg-1",
        child_profile_id="c1",
        mode_id="dialog",
        user_text="hi",
        short_term=stm,
    )
    assert "ok" in r.text.lower() or r.text
    await gw.aclose()
    get_settings.cache_clear()
