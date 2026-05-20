# Решения команды (center_voice_agent)

Документ фиксирует договорённости. Обновляйте при изменении инфраструктуры.

## Продукт и репозиторий

| Решение | Значение |
|---------|----------|
| Расположение кода | Папка `center_voice_agent/` в монорепо [arina](https://github.com/gorunovaalbina9-droid/arina) |
| Ветка с полным кодом агента на GitHub | **`center-voice-agent`** (до очистки `master` от файлов >100 MB) |
| Отдельный продуктовый UI профиля ребёнка | **Не в scope** — только схема БД и `child_profile_id` |

## Python

| Решение | Значение |
|---------|----------|
| Версия для разработки и CI | **3.11 или 3.12** (`requires-python >=3.11` в `pyproject.toml`) |
| Python 3.14 | Допустим локально, но LangChain может выдавать предупреждения — не целевая версия prod |

## LLM

| Решение | Значение |
|---------|----------|
| Протокол | OpenAI-compatible HTTP API (`ChatOpenAI`, `LLM_BASE_URL`) |
| Параметры | `LLM_API_KEY`, `LLM_MODEL` в `center_voice_agent/.env` (не коммитить) |
| Запасной ключ | `OPENAI_API_KEY` / `LLM_FALLBACK_ENV_FILE` / `config/agent.yaml` → только в `Settings` |
| Несекретные лимиты | `config/agent.yaml` + переопределение через `.env` |
| Слои | `AppContainer` → `SessionCoordinator` → `AgentGateway` + `TurnPromptBuilder` + `run_tool_loop` |
| Память в tools | `child_profile_id` сессии, не аргумент LLM |
| Tool-calling | Предпочтительно нативное (OpenAI-формат). **Plan B реализован:** `TEXT_TOOL_FALLBACK=true` — JSON в тексте ответа → `gateway_text_tool_fallback` → выполнение tool |

## Критерий «первый рабочий день»

1. `python -m center_voice_agent.cli.setup_check` без ошибок.
2. `python -m center_voice_agent.cli.live_acceptance` с заполненным `.env` — приёмка блока 2.
3. В логах: `correlation_id`, `gateway_in`, `gateway_out` (см. `docs/log_example_gateway.jsonl`).
4. `memory_upsert` → SQLite → `memory_search` (нативные tools или plan B).

## Голос

| Решение | Значение |
|---------|----------|
| ASR / TTS | Вне пакета (`13_reber`, `voice_assistant`); агент — **текстовый** |
| Контракт | Текст пользователя → `SessionCoordinator.handle_user_turn` → текст ответа (+ опционально `reply_spoken`) |

## ПДн в логах

По умолчанию в лог **не** пишется полный текст ребёнка (`LOG_REDACT_USER_TEXT=true`). См. `settings.py`.
