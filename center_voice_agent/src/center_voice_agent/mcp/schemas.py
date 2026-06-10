"""JSON Schema инструментов для MCP и внешних клиентов."""

from __future__ import annotations

from typing import Any

TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "memory_search": {
        "name": "memory_search",
        "description": (
            "Ищет записи в долгосрочной памяти о текущем ребёнке по смыслу запроса."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Поисковый запрос"},
                "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
            },
            "required": ["query"],
        },
    },
    "memory_upsert": {
        "name": "memory_upsert",
        "description": "Сохраняет факт в долгосрочную память текущего ребёнка.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["name", "hobby", "preference", "progress", "note"],
                },
                "value_text": {"type": "string"},
                "key": {"type": "string"},
            },
            "required": ["category", "value_text"],
        },
    },
    "web_search": {
        "name": "web_search",
        "description": "Поиск в интернете по запросу пользователя.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    "rag_search": {
        "name": "rag_search",
        "description": "Поиск по локальным методичкам центра (.md/.txt в RAG_DOCS_DIR).",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
}


def list_tool_schemas(*, tool_ids: frozenset[str] | None = None) -> list[dict[str, Any]]:
    ids = tool_ids or frozenset(TOOL_SCHEMAS.keys())
    out: list[dict[str, Any]] = []
    for tid in sorted(ids):
        schema = TOOL_SCHEMAS.get(tid)
        if schema is not None:
            out.append(dict(schema))
    return out
