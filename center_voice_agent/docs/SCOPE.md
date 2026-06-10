# Границы продукта (scope)

## В этом репозитории (`center_voice_agent`)

| Компонент | Статус |
|-----------|--------|
| SessionCoordinator + AgentGateway | Ядро диалога |
| HTTP `POST /turn`, WebSocket `/ws/session` | API для интеграций |
| Режимы, сценарии, LTM/STM | YAML + БД |
| Tool registry + MCP stdio | `tools/registry.py`, `python -m center_voice_agent.mcp` |
| Keyword RAG по локальным `.md` | `rag_search` (выключен по умолчанию) |
| NLU смены режима | exact + fuzzy (`modes/nlu.py`) |
| SQLite / PostgreSQL миграции | `db/migrations/{sqlite,postgresql}/` + Alembic baseline |

## Вне репозитория (отдельные продукты)

| # | Компонент | Где / как |
|---|-----------|-----------|
| 28 | **STT/TTS** | Пакет `voice_assistant` или внешний сервис; см. [VOICE_INTEGRATION.md](VOICE_INTEGRATION.md) |
| 29 | **Веб / личный кабинет родителя** | Отдельный frontend + backend; этот пакет — только API агента |
| 30 | **Production RAG** | Векторная БД, ingestion pipeline — за пределами keyword-stub |
| — | Полноценная модерация ML | Roadmap; сейчас regex + HTTP API + эскалация |

## Запуск API

```bash
pip install center-voice-agent[api]
center-agent-api
# POST http://127.0.0.1:8000/turn
# WS   ws://127.0.0.1:8000/ws/session
```

Подробнее: [API.md](API.md).
