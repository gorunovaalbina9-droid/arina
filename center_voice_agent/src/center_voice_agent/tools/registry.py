"""Реестр инструментов режима (расширение без правки factory)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from center_voice_agent.memory.repository import LongTermMemoryRepository

ToolBuilder = Callable[["ToolBuildContext"], Any]

_REGISTRY: dict[str, ToolBuilder] = {}


@dataclass
class ToolBuildContext:
    memory_repo: Optional[LongTermMemoryRepository]
    child_profile_id: str
    web_search_url: Optional[str] = None
    web_search_timeout_sec: float = 15.0
    tool_max_output_chars: int = 4000
    rag_docs_dir: Optional[Path] = None


def register_tool(tool_id: str, builder: ToolBuilder) -> None:
    _REGISTRY[tool_id] = builder


def build_tool(tool_id: str, ctx: ToolBuildContext) -> Any:
    builder = _REGISTRY.get(tool_id)
    if builder is None:
        raise KeyError(
            f"Неизвестный инструмент: {tool_id}. "
            "Зарегистрируйте в tools/builtin.py или config/modes."
        )
    return builder(ctx)


def registered_tool_ids() -> frozenset[str]:
    return frozenset(_REGISTRY.keys())


def clear_registry_for_tests() -> None:
    _REGISTRY.clear()
