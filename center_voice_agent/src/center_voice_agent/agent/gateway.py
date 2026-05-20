from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from center_voice_agent.age_bands.loader import load_age_bands, resolve_age_prompt
from center_voice_agent.agent.text_tool_fallback import parse_text_tool_calls
from center_voice_agent.agent.turn_langgraph import run_llm_tools_langgraph
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.db.session import create_engine_and_session_factory, ensure_sqlite_parent_dir
from center_voice_agent.logging_setup import text_fingerprint
from center_voice_agent.memory.repository import LongTermMemoryRepository
from center_voice_agent.modes.registry import ModeRegistry
from center_voice_agent.scenarios.graph_engine import ScenarioRuntime
from center_voice_agent.session.repo import SessionStateRepository
from center_voice_agent.settings import Settings, get_settings
from center_voice_agent.tools.factory import build_tools_for_mode
from center_voice_agent.tools.impl.web_search import truncate_tool_output

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
    reply_spoken: Optional[str] = None


class AgentGateway:
    """
    Единая точка входа (шлюз): режим из YAML, инструменты по списку, краткая память 15 реплик.
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

    @property
    def memory_repository(self) -> LongTermMemoryRepository:
        return self._memory

    async def aclose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None

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
        parsed = parse_text_tool_calls(text)
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
            if "child_profile_id" not in args:
                args["child_profile_id"] = child_profile_id
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

    async def _resolve_long_term_summary(
        self,
        child_profile_id: str,
        long_term_summary: Optional[str],
    ) -> Optional[str]:
        if long_term_summary is not None:
            return long_term_summary
        if not self.settings.prefetch_long_term_memory:
            return None
        await self._memory.ensure_child_profile(child_profile_id)
        return await self._memory.search(child_profile_id, "", limit=8)

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
        max_tool_chars = self.settings.tool_max_output_chars

        log.info(
            "modes_resolve",
            session_id=session_id,
            mode_id=mode_id,
            display_name=mode.display_name,
            tool_ids=mode.tool_ids,
        )

        tools = build_tools_for_mode(
            mode.tool_ids,
            memory_repo=self._memory,
            web_search_url=self.settings.web_search_url,
            web_search_timeout_sec=self.settings.web_search_timeout_sec,
            tool_max_output_chars=max_tool_chars,
        )

        llm_base = self._build_llm(mode.llm_params)
        if self._llm_override is None:
            llm = llm_base.bind_tools(tools)
        else:
            llm = llm_base

        tool_map = {t.name: t for t in tools}

        scenario_id = scenario.graph.id if scenario else None
        node_id = scenario.current_node_id if scenario else None

        gw_in: dict[str, Any] = {
            "session_id": session_id,
            "child_profile_id": child_profile_id,
            "mode_id": mode_id,
            "scenario_id": scenario_id,
            "scenario_node_id": node_id,
            "user_text_len": len(user_text),
            "age_band": age_band,
        }
        if self.settings.log_redact_user_text:
            gw_in["user_text_fp"] = text_fingerprint(user_text)
        else:
            gw_in["user_text"] = user_text
        log.info("gateway_in", **gw_in)

        short_term.append_user(user_text)

        node_hint = ""
        if scenario is not None:
            node_hint = scenario.current_node().prompt_to_model

        ltm = await self._resolve_long_term_summary(child_profile_id, long_term_summary)

        system_parts = [mode.system_prompt.strip()]
        age_block = resolve_age_prompt(self._age_bands, age_band)
        if age_block:
            system_parts.append("Настройка по возрасту (из конфигурации центра):\n" + age_block)
        if ltm:
            system_parts.append("Краткая долгосрочная память о ребёнке:\n" + ltm.strip())
        if node_hint:
            system_parts.append("Текущий этап сценария:\n" + node_hint.strip())

        messages: list[BaseMessage] = [
            SystemMessage(content="\n\n".join(system_parts)),
            *short_term.as_langchain(),
        ]

        t_llm0 = time.perf_counter()
        executed_tools: list[dict[str, Any]] = []
        rounds = 0

        if self.settings.use_langgraph:
            log.info("gateway_llm_engine", engine="langgraph", session_id=session_id)
            text, executed_tools, rounds = await run_llm_tools_langgraph(
                llm=llm,
                messages=messages,
                tool_map=tool_map,
                max_tool_rounds=max_rounds,
                tool_max_output_chars=max_tool_chars,
            )
            if rounds >= max_rounds:
                log.warning("gateway_tool_limit", session_id=session_id, rounds=rounds)
        else:
            log.info("gateway_llm_engine", engine="imperative", session_id=session_id)
            ai_msg = await llm.ainvoke(messages)
            if not isinstance(ai_msg, AIMessage):
                raise TypeError("Ожидался AIMessage от LLM")

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
                    out = truncate_tool_output(str(out), max_tool_chars)
                    messages.append(ToolMessage(content=out, tool_call_id=tid))
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

        if (
            self._llm_override is None
            and tools
            and not executed_tools
            and self.settings.text_tool_fallback
        ):
            text, fb_tools = await self._try_text_tool_fallback(
                llm=llm,
                messages=messages,
                text=text,
                tool_map=tool_map,
                child_profile_id=child_profile_id,
                session_id=session_id,
                max_tool_chars=max_tool_chars,
            )
            executed_tools.extend(fb_tools)

        llm_ms = int((time.perf_counter() - t_llm0) * 1000)

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
            llm_and_tools_ms=llm_ms,
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
            reply_spoken=text,
        )
