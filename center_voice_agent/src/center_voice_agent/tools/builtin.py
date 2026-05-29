"""Встроенные инструменты — регистрация при импорте."""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import StructuredTool, tool

from center_voice_agent.tools.impl import memory as memory_impl
from center_voice_agent.tools.impl import web_search as web_search_impl
from center_voice_agent.tools.registry import ToolBuildContext, register_tool

_MEMORY_SEARCH_DESC = (
    "Ищет записи в долгосрочной памяти о текущем ребёнке по смыслу запроса. "
    "Параметры: query (строка), limit (число, по умолчанию 5)."
)
_MEMORY_UPSERT_DESC = (
    "Сохраняет факт в долгосрочную память текущего ребёнка. "
    "category: name, hobby, preference, progress, note. "
    "value_text — текст факта; key — опционально для обновления записи."
)


def make_memory_search_tool(repo, *, child_profile_id: str) -> StructuredTool:
    async def _run(query: str, limit: int = 5) -> str:
        return await memory_impl.memory_search_text(
            repo, child_profile_id, query, limit=limit
        )

    return StructuredTool.from_function(
        coroutine=_run,
        name="memory_search",
        description=_MEMORY_SEARCH_DESC,
    )


def make_memory_upsert_tool(repo, *, child_profile_id: str) -> StructuredTool:
    async def _run(
        category: str,
        value_text: str,
        key: Optional[str] = None,
    ) -> str:
        return await memory_impl.memory_upsert_text(
            repo, child_profile_id, category, value_text, key=key
        )

    return StructuredTool.from_function(
        coroutine=_run,
        name="memory_upsert",
        description=_MEMORY_UPSERT_DESC,
    )


def make_web_search_tool(
    *,
    api_url: Optional[str],
    timeout_sec: float,
    max_chars: int,
) -> Any:
    @tool
    async def web_search(query: str) -> str:
        """Поиск в интернете по запросу пользователя."""
        return await web_search_impl.run_web_search(
            query,
            api_url=api_url,
            timeout_sec=timeout_sec,
            max_chars=max_chars,
        )

    return web_search


def _build_memory_search(ctx: ToolBuildContext) -> StructuredTool:
    if ctx.memory_repo is None:
        raise ValueError("Режим запрашивает memory_search, но memory_repo не передан.")
    return make_memory_search_tool(ctx.memory_repo, child_profile_id=ctx.child_profile_id)


def _build_memory_upsert(ctx: ToolBuildContext) -> StructuredTool:
    if ctx.memory_repo is None:
        raise ValueError("Режим запрашивает memory_upsert, но memory_repo не передан.")
    return make_memory_upsert_tool(ctx.memory_repo, child_profile_id=ctx.child_profile_id)


def _build_web_search(ctx: ToolBuildContext) -> Any:
    return make_web_search_tool(
        api_url=ctx.web_search_url,
        timeout_sec=ctx.web_search_timeout_sec,
        max_chars=ctx.tool_max_output_chars,
    )


def _register_builtin_tools() -> None:
    register_tool("memory_search", _build_memory_search)
    register_tool("memory_upsert", _build_memory_upsert)
    register_tool("web_search", _build_web_search)


_register_builtin_tools()

__all__ = [
    "make_memory_search_tool",
    "make_memory_upsert_tool",
    "make_web_search_tool",
]
