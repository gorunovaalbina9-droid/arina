"""Вызов инструментов с привязкой к child_profile_id сессии."""

from __future__ import annotations

from typing import Any, Optional

import structlog

from center_voice_agent.tools.impl.web_search import truncate_tool_output

log = structlog.get_logger(__name__)

_MEMORY_TOOLS = frozenset({"memory_search", "memory_upsert"})


async def invoke_tool(
    tool_map: dict[str, Any],
    name: str,
    args: dict[str, Any],
    *,
    child_profile_id: str,
    max_chars: int,
    session_id: Optional[str] = None,
) -> str:
    tool_obj = tool_map.get(name)
    if tool_obj is None:
        return f"Неизвестный инструмент: {name}"
    safe_args = dict(args)
    if name in _MEMORY_TOOLS:
        attempted = safe_args.get("child_profile_id")
        if (
            attempted is not None
            and str(attempted).strip()
            and str(attempted) != child_profile_id
        ):
            log.warning(
                "security_incident",
                reason="tool_child_id_override",
                direction="tool",
                session_id=session_id,
                child_profile_id=child_profile_id,
                attempted_child_profile_id=str(attempted),
                tool=name,
            )
        safe_args.pop("child_profile_id", None)
    out = await tool_obj.ainvoke(safe_args)
    return truncate_tool_output(str(out), max_chars)
