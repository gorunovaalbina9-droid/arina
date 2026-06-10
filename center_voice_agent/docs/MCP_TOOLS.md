# Инструменты и MCP

Бизнес-логика инструментов — `src/center_voice_agent/tools/impl/`.
Регистрация — `tools/registry.py` + `tools/builtin.py` (импорт регистрирует builders).

## Принцип «одна логика — два входа»

1. **LangChain** — `StructuredTool` / `@tool` для `bind_tools` у LLM.
2. **MCP** — stdio-сервер `center-agent-mcp` (или `python -m center_voice_agent.mcp`):
   JSON Schema из `mcp/schemas.py`, вызов тех же impl-функций.

```bash
pip install center-voice-agent[mcp]
center-agent-mcp
```

`memory_search` / `memory_upsert` через standalone MCP требуют сессии агента с БД;
для них используйте HTTP `/turn` или LangChain в процессе агента.

## Список инструментов

| ID | Назначение |
|----|------------|
| `web_search` | Поиск в сети (выключен по умолчанию в детских режимах) |
| `memory_search` | Чтение долгой памяти из БД |
| `memory_upsert` | Запись фактов (whitelist категорий) |
| `rag_search` | Keyword-поиск по `.md/.txt` в `RAG_DOCS_DIR` (выключен по умолчанию) |

Режимы подключают инструменты списком `tool_ids` в YAML без изменения Python.

Сборка для хода: `build_tools_for_mode()` в `tools/factory.py`.
