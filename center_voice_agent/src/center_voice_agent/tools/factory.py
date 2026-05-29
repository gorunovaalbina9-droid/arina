from __future__ import annotations

from typing import Any, Optional

import center_voice_agent.tools.builtin  # noqa: F401 — регистрация в реестре
from center_voice_agent.memory.repository import LongTermMemoryRepository
from center_voice_agent.tools.registry import ToolBuildContext, build_tool

# Обратная совместимость импортов
from center_voice_agent.tools.builtin import (  # noqa: E402
    make_memory_search_tool,
    make_memory_upsert_tool,
    make_web_search_tool,
)


def build_tools_for_mode(
    tool_ids: list[str],
    *,
    memory_repo: Optional[LongTermMemoryRepository],
    child_profile_id: str,
    web_search_url: Optional[str] = None,
    web_search_timeout_sec: float = 15.0,
    tool_max_output_chars: int = 4000,
) -> list[Any]:
    """Собирает LangChain-инструменты для режима; память привязана к child_profile_id сессии."""
    ctx = ToolBuildContext(
        memory_repo=memory_repo,
        child_profile_id=child_profile_id,
        web_search_url=web_search_url,
        web_search_timeout_sec=web_search_timeout_sec,
        tool_max_output_chars=tool_max_output_chars,
    )
    return [build_tool(tid, ctx) for tid in tool_ids]
