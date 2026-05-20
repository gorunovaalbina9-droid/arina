from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import StructuredTool, tool

from center_voice_agent.memory.repository import LongTermMemoryRepository
from center_voice_agent.tools.impl import memory as memory_impl
from center_voice_agent.tools.impl import web_search as web_search_impl

_MEMORY_SEARCH_DESC = (
    "Ищет записи в долгосрочной памяти о текущем ребёнке по смыслу запроса. "
    "Параметры: query (строка), limit (число, по умолчанию 5)."
)
_MEMORY_UPSERT_DESC = (
    "Сохраняет факт в долгосрочную память текущего ребёнка. "
    "category: name, hobby, preference, progress, note. "
    "value_text — текст факта; key — опционально для обновления записи."
)


def make_memory_search_tool(
    repo: LongTermMemoryRepository,
    *,
    child_profile_id: str,
) -> StructuredTool:
    async def _run(query: str, limit: int = 5) -> str:
        return await memory_impl.memory_search_text(
            repo, child_profile_id, query, limit=limit
        )

    return StructuredTool.from_function(
        coroutine=_run,
        name="memory_search",
        description=_MEMORY_SEARCH_DESC,
    )


def make_memory_upsert_tool(
    repo: LongTermMemoryRepository,
    *,
    child_profile_id: str,
) -> StructuredTool:
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
    out: list[Any] = []
    for tid in tool_ids:
        if tid == "web_search":
            out.append(
                make_web_search_tool(
                    api_url=web_search_url,
                    timeout_sec=web_search_timeout_sec,
                    max_chars=tool_max_output_chars,
                )
            )
        elif tid == "memory_search":
            if memory_repo is None:
                raise ValueError("Режим запрашивает memory_search, но memory_repo не передан.")
            out.append(
                make_memory_search_tool(memory_repo, child_profile_id=child_profile_id)
            )
        elif tid == "memory_upsert":
            if memory_repo is None:
                raise ValueError("Режим запрашивает memory_upsert, но memory_repo не передан.")
            out.append(
                make_memory_upsert_tool(memory_repo, child_profile_id=child_profile_id)
            )
        else:
            raise KeyError(
                f"Неизвестный инструмент: {tid}. Добавьте в tools/factory.py или config/modes."
            )
    return out
