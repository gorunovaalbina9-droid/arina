from pathlib import Path

import pytest
import yaml

from center_voice_agent.scenarios.graph_engine import (
    ScenarioGraph,
    ScenarioRuntime,
    load_scenario,
    validate_scenario_graph,
)
from center_voice_agent.scenarios.loader import clear_scenario_scan_cache, load_scenario_by_id
from center_voice_agent.scenarios.phrases import ScenarioCommandsFile, try_parse_scenario_reset


def test_validate_scenario_rejects_bad_next(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(
        "id: bad\nentry: a\nnodes:\n  a:\n    title: A\n    transitions:\n      - when: turn_complete\n        next: ghost\n",
        encoding="utf-8",
    )
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    g = ScenarioGraph.model_validate(raw)
    with pytest.raises(ValueError, match="ghost"):
        validate_scenario_graph(g)


def test_three_node_linear_advances(tmp_path: Path) -> None:
    scen = tmp_path / "config" / "scenarios"
    scen.mkdir(parents=True)
    (scen / "t.yaml").write_text(
        """
id: three_lin
entry: n1
nodes:
  n1:
    title: "1"
    prompt_to_model: p1
    transitions:
      - when: turn_complete
        next: n2
  n2:
    title: "2"
    prompt_to_model: p2
    transitions:
      - when: turn_complete
        next: n3
  n3:
    title: "3"
    prompt_to_model: p3
    transitions: []
""",
        encoding="utf-8",
    )
    clear_scenario_scan_cache()
    g = load_scenario_by_id(scen, "three_lin")
    rt = ScenarioRuntime.start(g)
    assert rt.current_node_id == "n1"
    assert rt.advance_on_event("turn_complete") is True
    assert rt.current_node_id == "n2"
    assert rt.advance_on_event("turn_complete") is True
    assert rt.current_node_id == "n3"
    assert rt.advance_on_event("turn_complete") is False
    clear_scenario_scan_cache()


def test_interrupt_reset_to_entry(tmp_path: Path) -> None:
    scen = tmp_path / "sc"
    scen.mkdir()
    (scen / "x.yaml").write_text(
        """
id: rst
entry: a
nodes:
  a:
    title: A
    transitions:
      - when: turn_complete
        next: b
  b:
    title: B
    on_interrupt:
      action: reset_to_entry
    transitions:
      - when: turn_complete
        next: c
  c:
    title: C
    transitions: []
""",
        encoding="utf-8",
    )
    g = load_scenario(scen / "x.yaml")
    rt = ScenarioRuntime.resume(g, "b")
    rt.apply_interrupt()
    assert rt.current_node_id == "a"


def test_try_parse_scenario_reset() -> None:
    cmds = ScenarioCommandsFile(reset_phrases=["сбрось сценарий"])
    assert try_parse_scenario_reset("пожалуйста сбрось сценарий сейчас", commands=cmds) is True
    assert try_parse_scenario_reset("просто привет", commands=cmds) is False


@pytest.mark.asyncio
async def test_coordinator_persists_scenario_nodes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "s.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)

    from center_voice_agent.agent.fake_llm import StaticChatModel
    from center_voice_agent.agent.gateway import AgentGateway
    from center_voice_agent.context.short_term import ShortTermMemory
    from center_voice_agent.db.session import init_database
    from center_voice_agent.orchestration.coordinator import SessionCoordinator
    from center_voice_agent.settings import Settings, get_settings

    modes = tmp_path / "modes"
    modes.mkdir(parents=True)
    (modes / "dialog.yaml").write_text(
        "id: dialog\ndisplay_name: D\nsystem_prompt: sd\ntool_ids: []\n", encoding="utf-8"
    )
    scen = tmp_path / "config" / "scenarios"
    scen.mkdir(parents=True)
    (scen / "g.yaml").write_text(
        """
id: persist_demo
entry: n1
nodes:
  n1:
    title: "1"
    transitions:
      - when: turn_complete
        next: n2
  n2:
    title: "2"
    transitions:
      - when: turn_complete
        next: n3
  n3:
    title: "3"
    transitions: []
""",
        encoding="utf-8",
    )
    (tmp_path / "voice.yaml").write_text("entries: []\n", encoding="utf-8")
    (tmp_path / "sc_voice.yaml").write_text("reset_phrases: []\n", encoding="utf-8")
    (tmp_path / "age.yaml").write_text("default_block: ''\nbands: {}\n", encoding="utf-8")

    project_root = Path(__file__).resolve().parents[1]
    get_settings.cache_clear()
    settings = Settings(
        DATABASE_URL=url,
        project_root=tmp_path,
        modes_dir=modes,
        scenarios_dir=scen,
        voice_commands_path=tmp_path / "voice.yaml",
        scenario_commands_path=tmp_path / "sc_voice.yaml",
        age_bands_path=tmp_path / "age.yaml",
    )
    await init_database(project_root, settings.database_url)
    clear_scenario_scan_cache()

    gw = AgentGateway(settings=settings, llm=StaticChatModel(responses=["a", "b", "c"]))
    coord = SessionCoordinator(gw, settings=settings)
    stm = ShortTermMemory(max_turns=15)
    sid = "sess-sc-1"

    await gw.session_repository.ensure(sid, "child-1", default_mode_id="dialog")
    await gw.session_repository.attach_scenario(sid, "persist_demo")

    r1 = await coord.handle_user_turn(
        session_id=sid, child_profile_id="child-1", user_text="hi", short_term=stm
    )
    assert r1.scenario_node_id == "n2"
    row = await gw.session_repository.get(sid)
    assert row is not None and row.scenario_node_id == "n2"

    r2 = await coord.handle_user_turn(
        session_id=sid, child_profile_id="child-1", user_text="again", short_term=stm
    )
    assert r2.scenario_node_id == "n3"

    await gw.aclose()
    get_settings.cache_clear()
    clear_scenario_scan_cache()
