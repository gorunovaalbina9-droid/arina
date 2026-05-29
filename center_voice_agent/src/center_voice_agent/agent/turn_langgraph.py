"""
LangGraph: узлы agent <-> tools до исчерпания tool_calls или лимита раундов.
Сценарий (advance по узлу) остаётся в шлюзе после графа — см. AgentGateway.run_turn.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from center_voice_agent.tools.runtime import invoke_tool

log = structlog.get_logger(__name__)


class LlmToolGraphState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    tool_batches: int
    max_tool_rounds: int
    executed_tools: Annotated[list[dict[str, Any]], operator.add]


def _route_after_llm(state: LlmToolGraphState) -> Literal["tools", "end"]:
    last = state["messages"][-1]
    batches = int(state.get("tool_batches", 0))
    max_r = int(state.get("max_tool_rounds", 10))
    if isinstance(last, AIMessage) and last.tool_calls and batches < max_r:
        return "tools"
    return "end"


async def _agent_node(state: LlmToolGraphState, config: RunnableConfig) -> dict[str, Any]:
    configurable = config.get("configurable") or {}
    llm: BaseChatModel = configurable["llm"]
    out = await llm.ainvoke(state["messages"])
    return {"messages": [out]}


async def _tools_node(state: LlmToolGraphState, config: RunnableConfig) -> dict[str, Any]:
    configurable = config.get("configurable") or {}
    tool_map: dict[str, Any] = configurable["tool_map"]
    max_chars = int(configurable.get("tool_max_output_chars", 4000))
    child_profile_id: str = configurable["child_profile_id"]
    session_id: str | None = configurable.get("session_id")
    last = state["messages"][-1]
    if not isinstance(last, AIMessage) or not last.tool_calls:
        return {}
    tool_msgs: list[ToolMessage] = []
    batch_logs: list[dict[str, Any]] = []
    for tc in last.tool_calls:
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
        tool_msgs.append(ToolMessage(content=out, tool_call_id=tid))
        batch_logs.append({"name": name, "args": args, "id": tid})
    log.info(
        "langgraph_tool_batch",
        tool_names=[x["name"] for x in batch_logs],
        batch_index=state.get("tool_batches", 0) + 1,
    )
    return {
        "messages": tool_msgs,
        "tool_batches": state.get("tool_batches", 0) + 1,
        "executed_tools": batch_logs,
    }


_compiled: Any | None = None


def get_compiled_graph() -> Any:
    global _compiled
    if _compiled is None:
        g = StateGraph(LlmToolGraphState)
        g.add_node("agent", _agent_node)
        g.add_node("tools", _tools_node)
        g.set_entry_point("agent")
        g.add_conditional_edges("agent", _route_after_llm, {"tools": "tools", "end": END})
        g.add_edge("tools", "agent")
        _compiled = g.compile()
    return _compiled


def reset_compiled_graph_for_tests() -> None:
    global _compiled
    _compiled = None


def _compiled_graph() -> Any:
    return get_compiled_graph()


def final_assistant_text(messages: list[BaseMessage]) -> str:
    last = messages[-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return (
            "Слишком много шагов с инструментами за один раз. "
            "Давай упростим вопрос или попробуем снова чуть позже."
        )
    if isinstance(last, AIMessage):
        return str(last.content) if last.content else ""
    return ""


async def run_llm_tools_langgraph(
    *,
    llm: BaseChatModel,
    messages: list[BaseMessage],
    tool_map: dict[str, Any],
    max_tool_rounds: int,
    child_profile_id: str,
    tool_max_output_chars: int = 4000,
    session_id: str | None = None,
) -> tuple[str, list[dict[str, Any]], int]:
    """Возвращает (текст ответа, список tool-вызовов, число завершённых «батчей» tools)."""
    graph = _compiled_graph()
    max_r = max(1, int(max_tool_rounds))
    out = await graph.ainvoke(
        {
            "messages": list(messages),
            "tool_batches": 0,
            "max_tool_rounds": max_r,
            "executed_tools": [],
        },
        config={
            "configurable": {
                "llm": llm,
                "tool_map": tool_map,
                "tool_max_output_chars": tool_max_output_chars,
                "child_profile_id": child_profile_id,
                "session_id": session_id,
            },
            "recursion_limit": max(60, max_r * 8 + 12),
        },
    )
    text = final_assistant_text(out["messages"])
    executed = list(out.get("executed_tools") or [])
    batches = int(out.get("tool_batches", 0))
    return text, executed, batches
