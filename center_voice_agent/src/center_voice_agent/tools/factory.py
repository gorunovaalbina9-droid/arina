from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import StructuredTool

from center_voice_agent.memory.repository import LongTermMemoryRepository
from center_voice_agent.tools.builtin import web_search

_MEMORY_SEARCH_DESC = (
    "Ищет записи в долгосрочной памяти о ребёнке по смыслу запроса (текст, ключевые слова). "
    "Параметр child_profile_id должен совпадать с текущей сессией."
)
_MEMORY_UPSERT_DESC = (
    "Сохраняет или обновляет факт в долгосрочной памяти. Категории только из разрешённого списка: "
    "name, hobby, preference, progress, note. Для обновления существующей записи укажи key."
)


def make_memory_search_tool(repo: LongTermMemoryRepository) -> StructuredTool:
    async def _run(child_profile_id: str, query: str, limit: int = 5) -> str:
        return await repo.search(child_profile_id, query, limit=limit)

    return StructuredTool.from_function(
        coroutine=_run,
        name="memory_search",
        description=_MEMORY_SEARCH_DESC,
    )


def make_memory_upsert_tool(repo: LongTermMemoryRepository) -> StructuredTool:
    async def _run(
        child_profile_id: str,
        category: str,
        value_text: str,
        key: Optional[str] = None,
    ) -> str:
        return await repo.upsert(child_profile_id, category, value_text, key=key)

    return StructuredTool.from_function(
        coroutine=_run,
        name="memory_upsert",
        description=_MEMORY_UPSERT_DESC,
    )


def build_tools_for_mode(
    tool_ids: list[str],
    *,
    memory_repo: Optional[LongTermMemoryRepository],
) -> list[Any]:
    """Собирает LangChain-инструменты для режима; память требует memory_repo."""
    out: list[Any] = []
    for tid in tool_ids:
        if tid == "web_search":
            out.append(web_search)
        elif tid == "memory_search":
            if memory_repo is None:
                raise ValueError("Режим запрашивает memory_search, но memory_repo не передан в фабрику.")
            out.append(make_memory_search_tool(memory_repo))
        elif tid == "memory_upsert":
            if memory_repo is None:
                raise ValueError("Режим запрашивает memory_upsert, но memory_repo не передан в фабрику.")
            out.append(make_memory_upsert_tool(memory_repo))
        else:
            raise KeyError(
                f"Неизвестный инструмент: {tid}. Добавьте в tools/factory.py или проверьте config/modes."
            )
    return out
