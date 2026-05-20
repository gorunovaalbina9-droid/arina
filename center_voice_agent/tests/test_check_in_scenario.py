from pathlib import Path

from center_voice_agent.scenarios.graph_engine import ScenarioRuntime, load_scenario


def test_check_in_three_loads_and_advances_three_nodes() -> None:
    root = Path(__file__).resolve().parents[1]
    graph = load_scenario(root / "config" / "scenarios" / "check_in_three.yaml")
    rt = ScenarioRuntime.start(graph)
    assert rt.current_node_id == "greet"
    assert rt.advance_on_event("turn_complete")
    assert rt.current_node_id == "reflect"
    assert rt.advance_on_event("turn_complete")
    assert rt.current_node_id == "close"
    assert not rt.advance_on_event("turn_complete")
