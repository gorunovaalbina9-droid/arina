"""Вызов инструментов с привязкой к child_profile_id сессии."""

from __future__ import annotations

from typing import Any

from center_voice_agent.tools.impl.web_search import truncate_tool_output

_MEMORY_TOOLS = frozenset({"memory_search", "memory_upsert"})


async def invoke_tool(
    tool_map: dict[str, Any],
    name: str,
    args: dict[str, Any],
    *,
    child_profile_id: str,
    max_chars: int,
) -> str:
    tool_obj = tool_map.get(name)
    if tool_obj is None:
        return f"Неизвестный инструмент: {name}"
    safe_args = dict(args)
    if name in _MEMORY_TOOLS:
        safe_args.pop("child_profile_id", None)
    out = await tool_obj.ainvoke(safe_args)
    return truncate_tool_output(str(out), max_chars)
