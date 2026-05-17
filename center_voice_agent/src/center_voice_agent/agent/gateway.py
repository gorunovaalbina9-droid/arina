from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from center_voice_agent.age_bands.loader import load_age_bands, resolve_age_prompt
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.db.session import create_engine_and_session_factory, ensure_sqlite_parent_dir
from center_voice_agent.memory.repository import LongTermMemoryRepository
from center_voice_agent.agent.turn_langgraph import run_llm_tools_langgraph
from center_voice_agent.modes.registry import ModeRegistry
from center_voice_agent.scenarios.graph_engine import ScenarioRuntime
from center_voice_agent.session.repo import SessionStateRepository
from center_voice_agent.settings import Settings, get_settings
from center_voice_agent.tools.factory import build_tools_for_mode

log = structlog.get_logger(__name__)

_DEFAULT_MAX_TOOL_ROUNDS = 10


@dataclass
class AgentTurnResult:
    text: str
    mode_id: str
    scenario_id: Optional[str]
    scenario_node_id: Optional[str]
    tool_calls: list[dict[str, Any]]
    mode_changed: bool = False
    previous_mode_id: Optional[str] = None


class AgentGateway:
    """
    Единая точка входа (шлюз): режим из YAML, инструменты по списку, краткая память 15 реплик.
    Дальше сюда навешиваются LangGraph, MCP-клиент, модерация.
    """

    def __init__(
        self,
        *,
        settings: Optional[Settings] = None,
        llm: Optional[BaseChatModel] = None,
        memory_repository: Optional[LongTermMemoryRepository] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.modes = ModeRegistry(
            self.settings.modes_dir,
            project_root=self.settings.project_root,
            database_url=self.settings.database_url,
            modes_source=self.settings.modes_source,
            modes_center_id=self.settings.modes_center_id,
        )
        self._llm_override = llm
        self._age_bands = load_age_bands(self.settings.age_bands_path)

        ensure_sqlite_parent_dir(self.settings.database_url)
        self._engine, session_factory = create_engine_and_session_factory(self.settings.database_url)
        self._session_repo = SessionStateRepository(session_factory)
        if memory_repository is not None:
            self._memory = memory_repository
        else:
            self._memory = LongTermMemoryRepository(session_factory)

    @property
    def session_repository(self) -> SessionStateRepository:
        return self._session_repo

    async def aclose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None

    def _build_llm(self, mode_params: dict[str, Any]) -> BaseChatModel:
        if self._llm_override is not None:
            return self._llm_override
        if not self.settings.llm_api_key:
            raise RuntimeError("LLM_API_KEY не задан. Для демо передайте llm=StaticChatModel в AgentGateway.")
        return ChatOpenAI(
            model=self.settings.llm_model,
            temperature=float(mode_params.get("temperature", 0.5)),
            max_tokens=int(mode_params.get("max_tokens", 512)),
            base_url=self.settings.llm_base_url,
            api_key=self.settings.llm_api_key,
        )

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
        skip_scenario_advance: bool = False,
    ) -> AgentTurnResult:
        t0 = time.perf_counter()
        mode = self.modes.get(mode_id)
        max_rounds = mode.max_tool_rounds or _DEFAULT_MAX_TOOL_ROUNDS

        log.info(
            "modes_resolve",
            session_id=session_id,
            mode_id=mode_id,
            display_name=mode.display_name,
            tool_ids=mode.tool_ids,
        )

        tools = build_tools_for_mode(mode.tool_ids, memory_repo=self._memory)

        llm_base = self._build_llm(mode.llm_params)
        if self._llm_override is None:
            llm = llm_base.bind_tools(tools)
        else:
            llm = llm_base

        tool_map = {t.name: t for t in tools}

        scenario_id = scenario.graph.id if scenario else None
        node_id = scenario.current_node_id if scenario else None

        log.info(
            "gateway_in",
            session_id=session_id,
            child_profile_id=child_profile_id,
            mode_id=mode_id,
            scenario_id=scenario_id,
            scenario_node_id=node_id,
            user_text_len=len(user_text),
            age_band=age_band,
        )

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

        messages: list[BaseMessage] = [
            SystemMessage(content="\n\n".join(system_parts)),
            *short_term.as_langchain(),
        ]

        if self.settings.use_langgraph:
            log.info("gateway_llm_engine", engine="langgraph", session_id=session_id)
            text, executed_tools, rounds = await run_llm_tools_langgraph(
                llm=llm,
                messages=messages,
                tool_map=tool_map,
                max_tool_rounds=max_rounds,
            )
            if rounds >= max_rounds:
                log.warning("gateway_tool_limit", session_id=session_id, rounds=rounds)
        else:
            log.info("gateway_llm_engine", engine="imperative", session_id=session_id)
            ai_msg = await llm.ainvoke(messages)
            if not isinstance(ai_msg, AIMessage):
                raise TypeError("Ожидался AIMessage от LLM")

            executed_tools = []
            rounds = 0

            while ai_msg.tool_calls and rounds < max_rounds:
                rounds += 1
                log.info(
                    "gateway_tool_round",
                    session_id=session_id,
                    round=rounds,
                    tool_names=[tc.get("name") for tc in ai_msg.tool_calls],
                )
                messages.append(ai_msg)
                for tc in ai_msg.tool_calls:
                    name = str(tc.get("name", ""))
                    tid = str(tc.get("id", ""))
                    args = tc.get("args") or {}
                    if not isinstance(args, dict):
                        args = dict(args) if hasattr(args, "items") else {}
                    tool_obj = tool_map.get(name)
                    if tool_obj is None:
                        out = f"Неизвестный инструмент: {name}"
                    else:
                        out = await tool_obj.ainvoke(args)
                    messages.append(ToolMessage(content=str(out), tool_call_id=tid))
                    executed_tools.append({"name": name, "args": args, "id": tid})

                ai_msg = await llm.ainvoke(messages)
                if not isinstance(ai_msg, AIMessage):
                    raise TypeError("Ожидался AIMessage от LLM после инструментов")

            if ai_msg.tool_calls:
                text = (
                    "Слишком много шагов с инструментами за один раз. "
                    "Давай упростим вопрос или попробуем снова чуть позже."
                )
                log.warning("gateway_tool_limit", session_id=session_id, rounds=rounds)
            else:
                text = str(ai_msg.content) if ai_msg.content else ""

        short_term.append_assistant(text)

        if scenario is not None and not skip_scenario_advance:
            scenario.advance_on_event("turn_complete")

        dt_ms = int((time.perf_counter() - t0) * 1000)
        log.info(
            "gateway_out",
            session_id=session_id,
            mode_id=mode_id,
            scenario_id=scenario_id,
            scenario_node_id=scenario.current_node_id if scenario else None,
            latency_ms=dt_ms,
            reply_len=len(text),
            tool_calls=len(executed_tools),
            tool_rounds=rounds,
        )

        return AgentTurnResult(
            text=text,
            mode_id=mode_id,
            scenario_id=scenario_id,
            scenario_node_id=scenario.current_node_id if scenario else None,
            tool_calls=executed_tools,
        )
