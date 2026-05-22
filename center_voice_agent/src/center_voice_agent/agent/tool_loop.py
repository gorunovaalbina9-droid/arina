"""
Единый цикл LLM ↔ tools (LangGraph или imperative — из Settings).
"""

from __future__ import annotations

from typing import Any, Callable, Awaitable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

import structlog

from center_voice_agent.agent.turn_langgraph import run_llm_tools_langgraph
from center_voice_agent.settings import Settings
from center_voice_agent.tools.runtime import invoke_tool
from center_voice_agent.tools.impl.web_search import truncate_tool_output

log = structlog.get_logger(__name__)

TextFallbackFn = Callable[
    [BaseChatModel, list[BaseMessage], str, dict[str, Any], str, str, int],
    Awaitable[tuple[str, list[dict[str, Any]]]],
]


async def run_tool_loop(
    settings: Settings,
    *,
    llm: BaseChatModel,
    messages: list[BaseMessage],
    tool_map: dict[str, Any],
    max_tool_rounds: int,
    session_id: str,
    child_profile_id: str,
    bind_tools: bool,
    text_fallback: TextFallbackFn | None = None,
) -> tuple[str, list[dict[str, Any]], int]:
    max_chars = settings.tool_max_output_chars
    max_r = max(1, int(max_tool_rounds))

    if settings.use_langgraph:
        log.info("gateway_llm_engine", engine="langgraph", session_id=session_id)
        text, executed, rounds = await run_llm_tools_langgraph(
            llm=llm,
            messages=messages,
            tool_map=tool_map,
            max_tool_rounds=max_r,
            tool_max_output_chars=max_chars,
            child_profile_id=child_profile_id,
            session_id=session_id,
        )
        if rounds >= max_r:
            log.warning("gateway_tool_limit", session_id=session_id, rounds=rounds)
        if bind_tools and tool_map and not executed and text_fallback and settings.text_tool_fallback:
            text, fb = await text_fallback(
                llm, messages, text, tool_map, child_profile_id, session_id, max_chars
            )
            executed.extend(fb)
        return text, executed, rounds

    log.info("gateway_llm_engine", engine="imperative", session_id=session_id)
    ai_msg = await llm.ainvoke(messages)
    if not isinstance(ai_msg, AIMessage):
        raise TypeError("Ожидался AIMessage от LLM")

    executed: list[dict[str, Any]] = []
    rounds = 0

    while ai_msg.tool_calls and rounds < max_r:
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
            out = await invoke_tool(
                tool_map,
                name,
                args,
                child_profile_id=child_profile_id,
                max_chars=max_chars,
                session_id=session_id,
            )
            messages.append(ToolMessage(content=out, tool_call_id=tid))
            executed.append({"name": name, "args": args, "id": tid})

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

    if bind_tools and tool_map and not executed and text_fallback and settings.text_tool_fallback:
        text, fb = await text_fallback(
            llm, messages, text, tool_map, child_profile_id, session_id, max_chars
        )
        executed.extend(fb)

    return text, executed, rounds
