from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

from center_voice_agent.agent.llm_client import build_chat_model
from center_voice_agent.agent.llm_provider import LLMProvider
from center_voice_agent.agent.memory_prefetch import resolve_long_term_summary
from center_voice_agent.agent.text_tool_fallback import parse_text_tool_calls
from center_voice_agent.agent.tool_loop import run_tool_loop
from center_voice_agent.agent.turn_metrics import TurnTimings, log_gateway_in, log_gateway_out, log_modes_resolve
from center_voice_agent.context.short_term import ShortTermMemory

if TYPE_CHECKING:
    from center_voice_agent.composition.container import AppContainer
from center_voice_agent.memory.repository import LongTermMemoryRepository
from center_voice_agent.modes.registry import ModeRegistry
from center_voice_agent.scenarios.graph_engine import ScenarioRuntime
from center_voice_agent.session.repo import SessionStateRepository
from center_voice_agent.security.redact import redact_tool_calls
from center_voice_agent.settings import Settings
from center_voice_agent.tools.factory import build_tools_for_mode
from center_voice_agent.tools.impl.web_search import truncate_tool_output

log = structlog.get_logger(__name__)


@dataclass
class AgentTurnResult:
    text: str
    mode_id: str
    scenario_id: Optional[str]
    scenario_node_id: Optional[str]
    tool_calls: list[dict[str, Any]]
    mode_changed: bool = False
    previous_mode_id: Optional[str] = None
    reply_spoken: Optional[str] = None


class AgentGateway:
    """
    Шлюз хода: промпт + LLM + tools (метрики, prefetch, advance сценария — снаружи).
    """

    def __init__(
        self,
        *,
        container: Optional["AppContainer"] = None,
        settings: Optional[Settings] = None,
        llm: Optional[BaseChatModel] = None,
        memory_repository: Optional[LongTermMemoryRepository] = None,
        llm_provider: Optional[LLMProvider] = None,
    ) -> None:
        if container is not None:
            self._container = container
        else:
            from center_voice_agent.composition.container import AppContainer

            self._container = AppContainer.from_settings(
                settings,
                memory_repository=memory_repository,
            )
        self.settings = self._container.settings
        self._llm_override = llm
        self._llm_provider = llm_provider
        self._prompt_builder = self._container.prompt_builder

    @property
    def modes(self) -> ModeRegistry:
        return self._container.mode_registry

    @property
    def session_repository(self) -> SessionStateRepository:
        return self._container.session_repository

    @property
    def memory_repository(self) -> LongTermMemoryRepository:
        return self._container.memory_repository

    @property
    def container(self) -> "AppContainer":
        return self._container

    async def aclose(self) -> None:
        await self._container.aclose()

    async def _try_text_tool_fallback(
        self,
        *,
        llm: BaseChatModel,
        messages: list[BaseMessage],
        text: str,
        tool_map: dict[str, Any],
        child_profile_id: str,
        session_id: str,
        max_tool_chars: int,
    ) -> tuple[str, list[dict[str, Any]]]:
        parsed = parse_text_tool_calls(
            text,
            mode=self.settings.text_tool_fallback_mode,
            allowed_tools=tuple(tool_map.keys()),
        )
        parsed = [c for c in parsed if c["name"] in tool_map]
        if not parsed:
            return text, []
        log.info(
            "gateway_text_tool_fallback",
            session_id=session_id,
            tool_names=[c["name"] for c in parsed],
        )
        executed: list[dict[str, Any]] = []
        tool_msgs: list[ToolMessage] = []
        for call in parsed:
            name = call["name"]
            args = dict(call["args"])
            tool_obj = tool_map.get(name)
            if tool_obj is None:
                out = f"Неизвестный инструмент: {name}"
            else:
                out = await tool_obj.ainvoke(args)
            out = truncate_tool_output(str(out), max_tool_chars)
            tid = f"text-fb-{len(executed)}"
            tool_msgs.append(ToolMessage(content=out, tool_call_id=tid))
            executed.append({"name": name, "args": args, "id": tid, "source": "text_fallback"})
        messages.append(AIMessage(content=text))
        messages.extend(tool_msgs)
        ai_msg = await llm.ainvoke(messages)
        if not isinstance(ai_msg, AIMessage):
            return text, executed
        new_text = str(ai_msg.content) if ai_msg.content else text
        return new_text, executed

    async def run_turn(
        self,
        *,
        session_id: str,
        child_profile_id: str,
        mode_id: str,
        user_text: str,
        short_term: ShortTermMemory,
        scenario: Optional[ScenarioRuntime] = None,
        long_term_summary: Optional[str] = None,
        age_band: Optional[str] = None,
        system_note: Optional[str] = None,
    ) -> AgentTurnResult:
        t0 = time.perf_counter()
        mode = self.modes.get(mode_id)
        max_rounds = mode.max_tool_rounds or self.settings.default_max_tool_rounds
        max_tool_chars = self.settings.tool_max_output_chars

        tools = build_tools_for_mode(
            mode.tool_ids,
            memory_repo=self.memory_repository,
            child_profile_id=child_profile_id,
            web_search_url=self.settings.web_search_url,
            web_search_timeout_sec=self.settings.web_search_timeout_sec,
            tool_max_output_chars=max_tool_chars,
            web_search_enabled=self.settings.web_search_enabled,
            mode_id=mode_id,
            web_search_allowed_mode_ids=self.settings.web_search_allowed_mode_ids,
        )

        llm_base = build_chat_model(
            self.settings,
            mode.llm_params,
            override=self._llm_override,
            provider=self._llm_provider,
        )
        bind_tools = self._llm_override is None
        llm = llm_base.bind_tools(tools) if tools else llm_base
        tool_map = {t.name: t for t in tools}
        modes_resolve_ms = int((time.perf_counter() - t0) * 1000)

        scenario_id = scenario.graph.id if scenario else None
        node_id = scenario.current_node_id if scenario else None

        log_modes_resolve(
            session_id=session_id,
            mode_id=mode_id,
            display_name=mode.display_name,
            tool_ids=mode.tool_ids,
            modes_resolve_ms=modes_resolve_ms,
        )
        log_gateway_in(
            self.settings,
            session_id=session_id,
            child_profile_id=child_profile_id,
            mode_id=mode_id,
            user_text=user_text,
            scenario_id=scenario_id,
            scenario_node_id=node_id,
            age_band=age_band,
        )

        t_prefetch0 = time.perf_counter()
        ltm = await resolve_long_term_summary(
            self.memory_repository,
            self.settings,
            child_profile_id,
            long_term_summary=long_term_summary,
        )
        memory_prefetch_ms = int((time.perf_counter() - t_prefetch0) * 1000)
        messages = self._prompt_builder.build_messages(
            mode=mode,
            user_text=user_text,
            short_term=short_term,
            long_term_summary=ltm,
            age_band=age_band,
            scenario=scenario,
            system_note=system_note,
        )

        t_llm0 = time.perf_counter()
        text, executed_tools, rounds = await run_tool_loop(
            self.settings,
            llm=llm,
            messages=messages,
            tool_map=tool_map,
            max_tool_rounds=max_rounds,
            session_id=session_id,
            child_profile_id=child_profile_id,
            bind_tools=bind_tools,
            text_fallback=self._try_text_tool_fallback if bind_tools else None,
        )
        llm_ms = int((time.perf_counter() - t_llm0) * 1000)

        short_term.append_assistant(text)

        timings = TurnTimings(
            modes_resolve_ms=modes_resolve_ms,
            memory_prefetch_ms=memory_prefetch_ms,
            llm_ms=llm_ms,
            total_ms=int((time.perf_counter() - t0) * 1000),
        )
        log_gateway_out(
            session_id=session_id,
            mode_id=mode_id,
            scenario_id=scenario_id,
            scenario_node_id=node_id,
            reply_len=len(text),
            tool_calls=len(executed_tools),
            tool_rounds=rounds,
            timings=timings,
        )

        safe_tools = redact_tool_calls(
            executed_tools,
            redact_args=self.settings.log_redact_tool_args,
        )

        return AgentTurnResult(
            text=text,
            mode_id=mode_id,
            scenario_id=scenario_id,
            scenario_node_id=node_id,
            tool_calls=safe_tools,
            reply_spoken=text,
        )
