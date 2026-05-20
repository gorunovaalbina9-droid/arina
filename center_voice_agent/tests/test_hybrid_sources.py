"""Стенды hybrid: modes_publish и scenarios_publish (цели 5.2, 6.5)."""

from pathlib import Path

import pytest

from center_voice_agent.modes.db_source import publish_mode_yaml_sync
from center_voice_agent.modes.registry import ModeRegistry
from center_voice_agent.scenarios.db_source import publish_scenario_yaml_sync
from center_voice_agent.scenarios.loader import clear_scenario_scan_cache, load_scenario_graph_unified


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_modes_hybrid_overlay(tmp_path: Path) -> None:
    from center_voice_agent.db.session import create_engine_and_session_factory, run_migrations

    db = tmp_path / "hy.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    engine, _ = create_engine_and_session_factory(url)
    await run_migrations(engine, PROJECT_ROOT)
    await engine.dispose()

    modes = tmp_path / "modes"
    modes.mkdir()
    (modes / "m.yaml").write_text(
        "id: ov\ndisplay_name: O\nsystem_prompt: from file\n", encoding="utf-8"
    )
    publish_mode_yaml_sync(
        url,
        config_yaml="id: ov\ndisplay_name: O\nsystem_prompt: from database\n",
        mode_id="ov",
        status="published",
    )
    reg = ModeRegistry(
        modes,
        project_root=tmp_path,
        database_url=url,
        modes_source="hybrid",
    )
    reg.reload_all()
    assert "from database" in reg.get("ov").system_prompt


@pytest.mark.asyncio
async def test_scenarios_hybrid_overlay(tmp_path: Path) -> None:
    from center_voice_agent.db.session import create_engine_and_session_factory, run_migrations

    db = tmp_path / "hy2.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    engine, _ = create_engine_and_session_factory(url)
    await run_migrations(engine, PROJECT_ROOT)
    await engine.dispose()

    scen = tmp_path / "scenarios"
    scen.mkdir()
    (scen / "s.yaml").write_text(
        "id: sc\nentry: a\nnodes:\n  a:\n    title: A\n    prompt_to_model: file\n    transitions: []\n",
        encoding="utf-8",
    )
    publish_scenario_yaml_sync(
        url,
        config_yaml="id: sc\nentry: a\nnodes:\n  a:\n    title: A\n    prompt_to_model: database\n    transitions: []\n",
        scenario_id="sc",
        status="published",
    )
    clear_scenario_scan_cache()
    g = load_scenario_graph_unified(scen, "sc", database_url=url, scenarios_source="hybrid")
    assert "database" in g.nodes["a"].prompt_to_model
    clear_scenario_scan_cache()
