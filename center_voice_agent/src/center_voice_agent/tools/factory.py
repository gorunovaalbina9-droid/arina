from __future__ import annotations

from pathlib import Path
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
    web_search_enabled: bool = False,
    mode_id: Optional[str] = None,
    web_search_allowed_mode_ids: tuple[str, ...] = (),
    rag_search_enabled: bool = False,
    rag_docs_dir: Optional[Path] = None,
) -> list[Any]:
    """Собирает LangChain-инструменты для режима; web_search/rag_search — только при включении."""
    effective_ids = list(tool_ids)
    if "web_search" in effective_ids:
        allowed = set(web_search_allowed_mode_ids or ())
        mode_ok = mode_id is None or not allowed or mode_id in allowed
        if not web_search_enabled or not mode_ok:
            effective_ids = [t for t in effective_ids if t != "web_search"]
    if "rag_search" in effective_ids and not rag_search_enabled:
        effective_ids = [t for t in effective_ids if t != "rag_search"]
    ctx = ToolBuildContext(
        memory_repo=memory_repo,
        child_profile_id=child_profile_id,
        web_search_url=web_search_url,
        web_search_timeout_sec=web_search_timeout_sec,
        tool_max_output_chars=tool_max_output_chars,
        rag_docs_dir=rag_docs_dir,
    )
    return [build_tool(tid, ctx) for tid in effective_ids]
