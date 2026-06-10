from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

import yaml
import structlog
from pydantic import BaseModel, Field, model_validator

from center_voice_agent.scenarios.transitions import normalize_transition_event, transition_matches

log = structlog.get_logger(__name__)

InterruptAction = Literal["stay", "reset_to_entry", "goto"]


class OnInterrupt(BaseModel):
    """Поведение при явном сбросе / прерывании сценария (фраза из конфига)."""

    action: InterruptAction = "stay"
    target: Optional[str] = None

    @model_validator(mode="after")
    def _goto_requires_target(self) -> OnInterrupt:
        if self.action == "goto" and not (self.target and str(self.target).strip()):
            raise ValueError("on_interrupt: для action=goto нужно непустое поле target")
        return self


class ScenarioTransition(BaseModel):
    when: str
    next: str


class ScenarioNode(BaseModel):
    title: str
    prompt_to_model: str = ""
    transitions: list[ScenarioTransition] = Field(default_factory=list)
    on_interrupt: Optional[OnInterrupt] = None


class ScenarioGraph(BaseModel):
    id: str
    version: int = 1
    entry: str
    nodes: dict[str, ScenarioNode]
    default_on_interrupt: OnInterrupt = Field(default_factory=OnInterrupt)

    @model_validator(mode="after")
    def _entry_exists(self) -> ScenarioGraph:
        if self.entry not in self.nodes:
            raise ValueError(f"entry «{self.entry}» отсутствует в nodes")
        return self


def validate_scenario_graph(graph: ScenarioGraph) -> None:
    """Проверка ссылок next, goto-target и непустых ключей узлов."""
    ids = frozenset(graph.nodes.keys())
    if graph.entry not in ids:
        raise ValueError(f"entry «{graph.entry}» не найден среди узлов")

    def check_on_interrupt(oi: OnInterrupt, *, ctx: str) -> None:
        if oi.action == "goto" and oi.target and oi.target not in ids:
            raise ValueError(f"{ctx}: on_interrupt.goto ведёт в неизвестный узел «{oi.target}»")

    check_on_interrupt(graph.default_on_interrupt, ctx="graph.default_on_interrupt")

    for nid, node in graph.nodes.items():
        if node.on_interrupt is not None:
            check_on_interrupt(node.on_interrupt, ctx=f"узел «{nid}»")
        for i, tr in enumerate(node.transitions):
            if tr.next not in ids:
                raise ValueError(
                    f"Узел «{nid}», переход #{i}: next «{tr.next}» не существует среди узлов сценария"
                )


def load_scenario(path: Path) -> ScenarioGraph:
    raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise ValueError(f"Ожидался объект YAML в {path}")
    graph = ScenarioGraph.model_validate(raw)
    validate_scenario_graph(graph)
    return graph


def load_scenario_yaml_string(yaml_text: str, *, source_hint: str = "database") -> ScenarioGraph:
    """Граф из строки YAML (таблица scenario_publish)."""
    raw = yaml.safe_load(yaml_text)
    if not isinstance(raw, dict):
        raise ValueError(f"Ожидался объект YAML в источнике {source_hint}")
    graph = ScenarioGraph.model_validate(raw)
    validate_scenario_graph(graph)
    return graph


def effective_on_interrupt(graph: ScenarioGraph, node_id: str) -> OnInterrupt:
    node = graph.nodes[node_id]
    if node.on_interrupt is not None:
        return node.on_interrupt
    return graph.default_on_interrupt


@dataclass
class ScenarioRuntime:
    """Текущее положение в графе сценария."""

    graph: ScenarioGraph
    vars: dict[str, object] = field(default_factory=dict)
    current_node_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.graph.entry not in self.graph.nodes:
            raise KeyError(f"entry «{self.graph.entry}» не найден")
        self.current_node_id = self.graph.entry

    @classmethod
    def start(cls, graph: ScenarioGraph) -> ScenarioRuntime:
        r = cls.__new__(cls)
        r.graph = graph
        r.vars = {}
        r.__post_init__()
        return r

    @classmethod
    def resume(
        cls,
        graph: ScenarioGraph,
        node_id: Optional[str],
        *,
        vars: Optional[dict[str, object]] = None,
    ) -> ScenarioRuntime:
        r = cls.__new__(cls)
        r.graph = graph
        r.vars = dict(vars or {})
        if node_id and node_id in graph.nodes:
            r.current_node_id = node_id
        else:
            r.current_node_id = graph.entry
        return r

    def current_node(self) -> ScenarioNode:
        if self.current_node_id not in self.graph.nodes:
            raise KeyError(f"Неизвестный узел графа: {self.current_node_id}")
        return self.graph.nodes[self.current_node_id]

    def _apply_transition(self, tr: ScenarioTransition, *, trigger: str, before: str) -> None:
        self.current_node_id = tr.next
        log.info(
            "scenario_transition",
            scenario_id=self.graph.id,
            from_node=before,
            to_node=self.current_node_id,
            when=tr.when,
            trigger=trigger,
        )

    def advance_on_user_text(self, user_text: str) -> bool:
        """Переходы when: keyword:... по тексту ребёнка (до LLM)."""
        node = self.current_node()
        before = self.current_node_id
        for tr in node.transitions:
            w = (tr.when or "").strip().lower()
            if not w.startswith("keyword:"):
                continue
            if transition_matches(tr.when, event="user_text", user_text=user_text):
                self._apply_transition(tr, trigger="user_keyword", before=before)
                return True
        return False

    def advance_on_user_mood(self, user_text: str) -> bool:
        """Переходы when: mood:... — смысловые группы слов после ответа LLM."""
        node = self.current_node()
        before = self.current_node_id
        for tr in node.transitions:
            w = (tr.when or "").strip().lower()
            if not w.startswith("mood:"):
                continue
            if transition_matches(tr.when, event="mood", user_text=user_text):
                self._apply_transition(tr, trigger="user_mood", before=before)
                return True
        return False

    def advance_on_event(self, event: str) -> bool:
        """
        Первое подходящее ребро: turn_complete / always (не keyword).
        """
        node = self.current_node()
        before = self.current_node_id
        ev = normalize_transition_event(event)
        for tr in node.transitions:
            w = (tr.when or "").strip()
            if w.lower().startswith("keyword:"):
                continue
            if transition_matches(tr.when, event=ev, user_text=""):
                self._apply_transition(tr, trigger=event, before=before)
                return True
        return False

    def apply_interrupt(self) -> dict[str, str]:
        """Политика on_interrupt для текущего узла (или default графа)."""
        pol = effective_on_interrupt(self.graph, self.current_node_id)
        before = self.current_node_id
        if pol.action == "stay":
            pass
        elif pol.action == "reset_to_entry":
            self.current_node_id = self.graph.entry
        elif pol.action == "goto" and pol.target:
            self.current_node_id = pol.target
        log.info(
            "scenario_interrupt",
            scenario_id=self.graph.id,
            action=pol.action,
            from_node=before,
            to_node=self.current_node_id,
        )
        return {"action": pol.action, "from_node": before, "to_node": self.current_node_id}

    def advance_default(self) -> str | None:
        """Обратная совместимость: при успешном переходе возвращает новый node_id, иначе None."""
        if self.advance_on_event("turn_complete"):
            return self.current_node_id
        return None
