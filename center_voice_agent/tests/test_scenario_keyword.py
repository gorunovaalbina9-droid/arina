from pathlib import Path

from center_voice_agent.scenarios.graph_engine import ScenarioRuntime, load_scenario
from center_voice_agent.scenarios.transitions import parse_when, transition_matches


def test_parse_keyword_when() -> None:
    kind, payload = parse_when("keyword:да,хорошо")
    assert kind == "keyword"
    assert payload == ("да", "хорошо")
    assert transition_matches("keyword:грустно", event="user_text", user_text="мне грустно")


def test_branch_mood_keyword_support() -> None:
    root = Path(__file__).resolve().parents[1]
    graph = load_scenario(root / "config" / "scenarios" / "branch_mood.yaml")
    rt = ScenarioRuntime.start(graph)
    assert rt.current_node_id == "ask_mood"
    assert rt.advance_on_user_text("мне сегодня грустно")
    assert rt.current_node_id == "support"


def test_branch_mood_keyword_happy() -> None:
    root = Path(__file__).resolve().parents[1]
    graph = load_scenario(root / "config" / "scenarios" / "branch_mood.yaml")
    rt = ScenarioRuntime.start(graph)
    assert rt.advance_on_user_text("всё отлично!")
    assert rt.current_node_id == "happy"
