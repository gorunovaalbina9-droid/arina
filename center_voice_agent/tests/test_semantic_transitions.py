"""Тесты semantic-переходов в сценариях."""

from center_voice_agent.scenarios.graph_engine import ScenarioGraph, ScenarioNode, ScenarioRuntime, ScenarioTransition
from center_voice_agent.scenarios.transitions import transition_matches


def _runtime() -> ScenarioRuntime:
    graph = ScenarioGraph(
        id="t",
        entry="a",
        nodes={
            "a": ScenarioNode(
                title="A",
                transitions=[
                    ScenarioTransition(
                        when="semantic:я готов продолжить|готов идти дальше",
                        next="b",
                    )
                ],
            ),
            "b": ScenarioNode(title="B"),
        },
    )
    return ScenarioRuntime.start(graph)


def test_semantic_transition_fuzzy() -> None:
    rt = _runtime()
    assert rt.advance_on_semantic("ну ладно, я готов продолжить", threshold=0.55)
    assert rt.current_node_id == "b"


def test_semantic_transition_matches_helper() -> None:
    assert transition_matches(
        "semantic:я расстроен|мне грустно",
        event="semantic",
        user_text="мне сейчас грустно",
        semantic_threshold=0.6,
    )
