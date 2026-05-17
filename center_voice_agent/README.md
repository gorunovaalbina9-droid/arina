# center_voice_agent

Обёртка агента на **LangChain** для голосового ИИ-наставника детского центра: динамические режимы, сценарии-граф, краткая/долгосрочная память, инструменты (в т.ч. под MCP), структурированное логирование.

## Быстрый старт (разработка)

```bash
cd center_voice_agent
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
python -m center_voice_agent.cli.init_db
python -m center_voice_agent.cli.reload_modes
python -m center_voice_agent.cli.demo_turn
python -m pytest tests/ -q
```

Подробный план этапов и приёмки: [docs/WORK_PLAN.md](docs/WORK_PLAN.md). Режимы и переключения: [docs/MODES.md](docs/MODES.md). Сценарии-граф: [docs/SCENARIOS.md](docs/SCENARIOS.md).

## Структура

- `config/modes/` — режимы (промпты, параметры LLM, список tools), правятся без перекомпиляции.
- `config/voice/mode_commands.yaml` — фразы для смены режима (плюс `voice_aliases` в YAML режимов).
- `config/voice/scenario_commands.yaml` — фразы сброса сценария (`reset_phrases`).
- `config/age_bands/default.yaml` — текстовые блоки по возрасту для системного промпта.
- `config/scenarios/` — графы сценариев по узлам-этапам.
- `db/migrations/` — схема БД для профиля-оболочки и долгой памяти.
- `src/center_voice_agent/memory/` — долгосрочная память (репозиторий + whitelist категорий).
- `src/center_voice_agent/db/` — async SQLAlchemy, миграции `001_init.sql`, `init_database()`.

Первая цель (БД + память + цикл tools в шлюзе) реализована: после `init_db` инструменты `memory_search` / `memory_upsert` ходят в SQLite; при реальном LLM шлюз выполняет до 10 раундов tool_calls (лимит переопределяется полем `max_tool_rounds` в режиме).

Вторая цель (режимы): три режима `dialog` / `lesson` / `play`, внешний промпт для диалога (`system_prompt_path`), `allowed_transitions`, словарь команд, **`SessionCoordinator`**, возрастной блок, логи `modes_resolve` и **`mode_registry_loaded`** (в т.ч. **`mode_files`** с mtime), CLI **`reload_modes`**, тест на отказ смены режима.

Третья цель (сценарии): YAML-граф в `config/scenarios/`, переходы по **`turn_complete`**, политика **`on_interrupt`**, загрузка по `id` из сессии (`attach_scenario`), фразы сброса, логи **`scenario_transition`** / **`scenario_interrupt`**, тесты на 3+ узла и персистентность указателя в БД; публикация графов в **`scenario_publish`**, **`SCENARIOS_SOURCE`**, CLI **`scenarios_publish`**, цикл LLM/tools через **LangGraph** (`USE_LANGGRAPH`).

## Тесты

```bash
python -m pytest tests/ -q
```

В git ведутся небольшие атомарные коммиты по спринтам; для контрольных точек используйте теги (`git tag`), см. план в `docs/WORK_PLAN.md`.
