# center_voice_agent

Обёртка агента на **LangChain** для голосового ИИ-наставника детского центра.

**Начните здесь:** [START_HERE.md](START_HERE.md) → подробная инструкция для вас: [docs/INSTRUKCIYA_DLYA_VAS.md](docs/INSTRUKCIYA_DLYA_VAS.md)

## GitHub

Код агента в монорепо [arina](https://github.com/gorunovaalbina9-droid/arina).

| Ветка | Назначение |
|-------|------------|
| **[`center-voice-agent`](https://github.com/gorunovaalbina9-droid/arina/tree/center-voice-agent/center_voice_agent)** | **Рабочая** — сюда коммитим и откуда клонируем агент |
| `master` | Весь монорепо; push может падать из‑за установщиков >100 MB в истории — см. [docs/GIT.md](docs/GIT.md) |

```bash
git clone -b center-voice-agent https://github.com/gorunovaalbina9-droid/arina.git
cd arina/center_voice_agent
```

Подробнее: **[docs/GIT.md](docs/GIT.md)** — ветки, PR, `.gitignore`, опциональная очистка истории.

## Python

Используйте **3.11 или 3.12** (см. `.python-version`). Python 3.14 — только для локальных экспериментов; в CI гоняются 3.11 и 3.12 (корень монорепо: `.github/workflows/center_voice_agent.yml`).

## Чеклист нового разработчика (блок 1)

Полный список: **[docs/SETUP_CHECKLIST.md](docs/SETUP_CHECKLIST.md)**.

| Шаг | Команда / действие |
|-----|-------------------|
| venv 3.12 | `py -3.12 -m venv .venv` → activate |
| Зависимости | `pip install -e ".[dev]"` |
| Конфиг | `copy .env.example .env` |
| БД | `python -m center_voice_agent.cli.init_db` |
| Демо | `python -m center_voice_agent.cli.demo_turn` |
| Тесты | `python -m pytest tests/ -q` |

**Приёмка:** любой разработчик за 1–2 часа проходит чеклист без правок кода.

## Первый рабочий день

Минимум для приёмки стенда с **реальным** LLM:

1. `init_db` без ошибок.
2. `python -m center_voice_agent.cli.live_turn Привет!` с заполненным `.env` — осмысленный ответ API.
3. В JSON-логах: `correlation_id`, `gateway_in`, `gateway_out`.
4. По желанию: запись в долгую память через tools (`memory_upsert` / `memory_search`).

Подробнее: [docs/DECISIONS.md](docs/DECISIONS.md).

## Быстрый старт

```bash
cd center_voice_agent
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
python -m center_voice_agent.cli.init_db
python -m center_voice_agent.cli.reload_modes
python -m center_voice_agent.cli.demo_turn
python -m pytest tests/ -q
```

## Реальный LLM

Заполните `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` в `.env`, затем:

```bash
python -m center_voice_agent.cli.live_turn Привет!
```

## Текстовый чат (без микрофона)

```bash
python -m center_voice_agent.cli.text_turn
python -m center_voice_agent.cli.text_turn --live
```

## CLI

| Команда | Назначение |
|---------|------------|
| `cli.init_db` | Миграции SQLite |
| `cli.reload_modes` | Перезагрузка YAML режимов |
| `cli.modes_publish` | Режим в таблицу `mode_definitions` |
| `cli.scenarios_publish` | Сценарий в `scenario_publish` |
| `cli.create_child` | Создать `child_profile` |
| `cli.setup_check` | Проверка Python, .env, БД, режимов |
| `cli.demo_turn` | Демо с fake LLM (`--live` — реальный API) |
| `cli.live_acceptance` | Приёмка блока 2 (диалог + память + логи) |
| `cli.memory_roundtrip` | Память upsert→search без LLM |
| `cli.live_turn` | Один ход с реальным API |
| `cli.live_acceptance` | Приёмка блока 2: API + память + логи |

## Документация

- [WORK_PLAN.md](docs/WORK_PLAN.md) — этапы и спринты
- [DECISIONS.md](docs/DECISIONS.md) — договорённости команды
- [SETUP_CHECKLIST.md](docs/SETUP_CHECKLIST.md) — чеклист окружения (1–2 ч)
- [GOALS.md](docs/GOALS.md) — чеклист мелких целей
- [MODES.md](docs/MODES.md) / [METHODIST.md](docs/METHODIST.md) — режимы
- [SCENARIOS.md](docs/SCENARIOS.md) — сценарии-граф
- [MEMORY_CATEGORIES.md](docs/MEMORY_CATEGORIES.md) — долгая память
- [GIT.md](docs/GIT.md) — ветки, клонирование, публикация

## Реализованные цели (кратко)

1. **Память + БД** — SQLite, tools, цикл tool_calls, LangGraph.
2. **Режимы** — YAML, координатор, БД, возрастные блоки.
3. **Сценарии** — граф, персистентность, publish в БД, сброс по фразам.

Дополнительно: prefetch памяти (`PREFETCH_LONG_TERM_MEMORY`), модерация-заглушка, `reply_spoken`, `WEB_SEARCH_URL`, логи без сырого текста (`LOG_REDACT_USER_TEXT`).
