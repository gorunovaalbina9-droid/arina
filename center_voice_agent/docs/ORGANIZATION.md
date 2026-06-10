# Организация кода (слои пакета)

| Слой | Путь | Назначение |
|------|------|------------|
| Ядро | `agent/`, `orchestration/`, `composition/` | Ход диалога, координатор, DI |
| Голос | `voice/` | Долгоживущие сессии для STT/TTS снаружи |
| Интеграция | `integration/bridge.py` | Низкоуровневый `AgentSession` |
| HTTP | `api/` | `POST /turn` (опционально `[api]`) |
| Админ | `admin/publish.py`, `admin/db_read.py` | Publish и чтение YAML из БД |
| CLI | `cli/` | Операции, приёмка, пилот |
| Ops docs | `docs/pilot/` | Пилот с детьми (не runtime) |

## Голос vs HTTP

- **Голос:** `center_voice_agent.voice.ask_voice_sync` — один `AppContainer` + кэш `AgentSession` на `session_id`.
- **HTTP:** `center_voice_agent.api` — тот же контейнер, stateless по запросу (STM в БД при `SHORT_TERM_SOURCE=db`).
- **Отладка:** `integration.bridge.ask_once_sync` — новая сессия на каждый вызов.

## БД

- Runtime и publish: **async** SQLAlchemy (`composition/runtime.py`, `admin/publish.py`).
- Чтение для reload режимов (sync): SQLAlchemy sync (`admin/db_read.py`), без `sqlite3` в бизнес-коде.
- Сценарии в ходе диалога: **async** read через `gateway.container.engine`.

## Миграции

`schema_migrations` + `006_scenario_definitions_legacy.sql` — рабочая схема `scenario_publish`.
