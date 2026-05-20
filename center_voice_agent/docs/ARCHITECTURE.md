# Архитектура center_voice_agent

## Конфигурация (главное правило)

| Слой | Откуда берёт настройки |
|------|-------------------------|
| **Settings** (`settings.py`) | `.env` + `config/agent.yaml` (не секреты) |
| **Режимы / сценарии / голос** | `config/modes/`, `config/scenarios/`, `config/voice/` |
| **Остальной код** | Только `Settings` или `AppContainer(settings=...)` |

Переменные окружения **не читаются** в gateway, tools, coordinator — только в `Settings`.

## Слои

```
CLI / integration.bridge
        │
        ▼
SessionCoordinator  — сессия, фразы режима/сценария, модерация
        │
        ▼
AgentGateway.run_turn  — один ход
        ├── TurnPromptBuilder   (системный промпт + short_term)
        ├── build_tools_for_mode(settings, child_profile_id)
        ├── build_chat_model(settings)
        └── run_tool_loop(settings)  → LangGraph или imperative
        │
AppContainer — БД, memory_repository, session_repository, ModeRegistry
```

## Безопасность памяти

`memory_search` / `memory_upsert` **не принимают** `child_profile_id` от модели — ID задаётся сессией при сборке tools.

## Что настраивать без Python

- `config/agent.yaml` — лимиты памяти, short_term, tool rounds
- `config/moderation.yaml` — фразы блокировки (модерация)
- `config/modes/*.yaml` — режимы, tool_ids, промпты
- `config/scenarios/*.yaml` — графы
- `config/voice/*.yaml` — фразы смены режима / сброса сценария
- `.env` — секреты LLM, БД, флаги (`USE_LANGGRAPH`, `PREFETCH_LONG_TERM_MEMORY`, …)

## Соответствие code review (кратко)

| Замечание | Статус |
|-----------|--------|
| env только в Settings | Да |
| child_profile_id не от LLM | Да (`tools/factory` + `tools/runtime`) |
| prefetch памяти | Да (`PREFETCH_LONG_TERM_MEMORY`) |
| модерация | Да (`config/moderation.yaml`) |
| god object gateway | Снято: `TurnPromptBuilder`, `run_tool_loop`, `AppContainer` |
| дубль tool-loop | Один вход: `run_tool_loop` (LangGraph / imperative) |
| correlation_id | Да (`logging_setup`, CLI) |
