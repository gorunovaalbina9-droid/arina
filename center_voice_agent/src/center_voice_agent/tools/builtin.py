from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


@tool
def web_search(query: str) -> str:
    """Поиск в интернете. Реализацию подменяет провайдер (API ключи в конфиге инфраструктуры)."""
    return (
        "[web_search заглушка] Запрос принят. Подключите провайдер поиска. "
        f"query={query!r}"
    )
