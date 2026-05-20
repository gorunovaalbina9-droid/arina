"""Сборка системного промпта и сообщений для хода (без LLM и tools)."""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.messages import BaseMessage, SystemMessage

from center_voice_agent.age_bands.loader import resolve_age_prompt
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.modes.schema import ModeConfig
from center_voice_agent.scenarios.graph_engine import ScenarioRuntime


class TurnPromptBuilder:
    def __init__(self, *, age_bands: dict[str, Any]) -> None:
        self._age_bands = age_bands

    def build_messages(
        self,
        *,
        mode: ModeConfig,
        user_text: str,
        short_term: ShortTermMemory,
        long_term_summary: Optional[str],
        age_band: Optional[str],
        scenario: Optional[ScenarioRuntime],
    ) -> list[BaseMessage]:
        short_term.append_user(user_text)

        node_hint = ""
        if scenario is not None:
            node_hint = scenario.current_node().prompt_to_model

        system_parts = [mode.system_prompt.strip()]
        age_block = resolve_age_prompt(self._age_bands, age_band)
        if age_block:
            system_parts.append("Настройка по возрасту (из конфигурации центра):\n" + age_block)
        if long_term_summary:
            system_parts.append("Краткая долгосрочная память о ребёнке:\n" + long_term_summary.strip())
        if node_hint:
            system_parts.append("Текущий этап сценария:\n" + node_hint.strip())

        return [
            SystemMessage(content="\n\n".join(system_parts)),
            *short_term.as_langchain(),
        ]
