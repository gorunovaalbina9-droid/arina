# ПОДРОБНОЕ ТЕХНИЧЕСКОЕ ЗАДАНИЕ
# Голосовой ИИ-наставник для детского центра (center_voice_agent)

Версия документа: 1.0 (сводка по репозиторию arina, ветка center-voice-agent)  
Дата актуализации: май 2026  
Репозиторий: https://github.com/gorunovaalbina9-droid/arina  
Папка кода: center_voice_agent/

Как открыть в Блокноте: Проводник → этот файл → ПКМ → «Открыть с помощью» → Блокнот.  
Или: notepad "...\center_voice_agent\docs\TZ_PODROBNOE.md"

Связанные документы (короткие версии):
- docs/WORK_PLAN.md — исходный план-ТЗ
- docs/GOALS.md — чеклист выполнения
- docs/BACKLOG.md — мелкие задачи по ID
- docs/DECISIONS.md — зафиксированные решения

================================================================================
1. НАЗНАЧЕНИЕ И ГРАНИЦЫ ПРОЕКТА
================================================================================

1.1. Цель продукта
-----------------
Создать программную обёртку (агент) вокруг языковой модели для детского
образовательного/развивающего центра. Ребёнок общается с наставником «Ариной»
голосом или текстом. Агент:
- ведёт диалог с учётом возраста и режима занятия;
- помнит контекст беседы и согласованные факты о ребёнке;
- может следовать сценарию урока (граф этапов);
- вызывает инструменты (память, поиск и т.д.) безопасно;
- логирует работу без утечки персональных данных в открытый вид.

1.2. Что НЕ входит в scope этого репозитория
--------------------------------------------
- Отдельный веб/UI «личный кабинет» профиля ребёнка (только схема в БД).
- Распознавание речи (ASR) и синтез речи (TTS) — внешние модули (voice_assistant,
  13_reber и т.п.); агент принимает и отдаёт ТЕКСТ.
- Обучение/дообучение модели (ожидается готовый HTTP API совместимый с OpenAI).
- Полноценный прод-сервер (PostgreSQL, Redis, Kubernetes) — этап развития;
  сейчас SQLite для разработки и пилота.

1.3. Пользователи системы
-------------------------
- Ребёнок — диалог (голос через оболочку или текст).
- Педагог — запуск сессии, наблюдение, пилот.
- Методист — редактирование режимов и сценариев (YAML), публикация в БД.
- Разработчик — код, деплой, логи.
- Юрист/центр — согласование полей памяти и сроков хранения.

================================================================================
2. АРХИТЕКТУРНЫЕ ПРИНЦИПЫ
================================================================================

2.1. Один шлюз (Gateway)
------------------------
Вся логика одного «хода» диалога проходит через AgentGateway.run_turn():
  вход: session_id, child_profile_id, user_text, режим, сценарий, краткая память
  выход: текст ответа, reply_spoken, метаданные (режим, узел сценария, tool_calls)

Над шлюзом — SessionCoordinator: смена режима по фразам, модерация, rate limit,
продвижение сценария, запись краткой памяти в БД (опционально).

2.2. Конфигурация без пересборки кода
-------------------------------------
Режимы: config/modes/*.yaml (+ опционально таблица mode_definitions в БД).
Сценарии: config/scenarios/*.yaml (+ scenario_publish в БД).
Голосовые команды: config/voice/mode_commands.yaml, scenario_commands.yaml.
Модерация: config/moderation.yaml.
Лимиты агента: config/agent.yaml.
Секреты: только .env (не в git).

2.3. Одна база данных (SQLite на этапе разработки)
---------------------------------------------------
Файл: center_voice_agent/data/agent.db
URL: DATABASE_URL в .env (по умолчанию sqlite+aiosqlite:///./data/agent.db)

В одной БД хранятся:
- профили детей (child_profiles);
- долгосрочная память (long_term_memory_entries);
- состояние сессии (session_state): режим, сценарий, узел;
- опционально реплики диалога (session_messages) при SHORT_TERM_SOURCE=db;
- опубликованные копии YAML режимов/сценариев (mode_definitions, scenario_publish).

Это НЕ «две базы», а разные таблицы одного файла SQLite.

2.4. Голосовой контур (вне агента)
----------------------------------
  [Микрофон] → ASR → текст
       → SessionCoordinator / AgentGateway
       → текст ответа (+ reply_spoken)
       → TTS → [динамик]

Мост: voice_assistant/center_agent_bridge.py
Флаг: USE_CENTER_AGENT=true
Без API: fake LLM (по умолчанию без CENTER_AGENT_LIVE=true)

2.5. Безопасность
-----------------
- child_profile_id для tools задаётся сессией, LLM не может подменить ID.
- Сырой текст ребёнка в логах по умолчанию НЕ пишется (LOG_REDACT_USER_TEXT=true).
- Модерация входа/выхода по спискам фраз (moderation.yaml).
- Rate limit на session_id.
- Журнал инцидентов: data/security_incidents.jsonl.

================================================================================
3. ФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ
================================================================================

3.1. Краткосрочная память (контекст диалога)
--------------------------------------------
Требование:
- Хранить последние N реплик user/assistant (N = SHORT_TERM_MAX_MESSAGES, default 15).
- Передавать в LLM как список LangChain BaseMessage.

Реализация:
- RAM: ShortTermMemory (deque), SHORT_TERM_SOURCE=memory (по умолчанию).
- БД: таблица session_messages, SHORT_TERM_SOURCE=db — восстановление после
  перезапуска процесса при том же session_id.

Приёмка:
- В одном ходе в промпт попадают предыдущие реплики + новая реплика user.
- Тест: test_session_messages_db.py, demo_turn.

3.2. Долгосрочная память
------------------------
Требование:
- Хранить факты о ребёнке по категориям (согласованным с юристом).
- Чтение: memory_search; запись: memory_upsert.
- Опционально prefetch в системный промпт (PREFETCH_LONG_TERM_MEMORY=true).

Разрешённые категории (MEMORY_CATEGORIES.md):
  name, hobby, preference, progress, note

Запрещено без юридического согласования:
  адрес, телефон, диагнозы, данные родителей и т.п.

Приёмка:
- memory_roundtrip CLI: upsert → SQLite → search.
- LIKE-поиск экранирует % и _ (тест test_memory_search_like_escape).

3.3. Режимы работы
------------------
Требование:
- Несколько режимов (dialog, lesson, play, calm, …) с разными:
  - system_prompt;
  - tool_ids (набор инструментов);
  - llm_params (temperature и т.д.);
  - allowed_transitions (какие режимы можно включить голосом/текстом).

Реализация:
- ModeRegistry загружает YAML; MODES_SOURCE=files|database|hybrid.
- modes_publish — копия YAML в БД; reload_modes — перечитать без рестарта.

Смена режима:
- Ребёнок/педагог говорит фразу из mode_commands.yaml → coordinator меняет mode_id
  в session_state или отвечает отказом с понятным текстом.

Приёмка:
- Новый YAML-режим работает без правки Python (кроме нового tool, если нужен).
- test_modes_schema, MODES_HYBRID_CHECKLIST.md.

3.4. Сценарии (граф урока)
--------------------------
Требование:
- Сценарий = граф узлов (этапов) с prompt_to_model и переходами (when).
- Типы when: turn_complete, always, keyword:слово1,слово2.
- Сброс сценария по фразам (on_interrupt, scenario_commands.yaml).
- Состояние: scenario_id + scenario_node_id в session_state.

Реализация:
- ScenarioRuntime, transitions.py;
- advance после ответа LLM (в gateway) + keyword до LLM (coordinator);
- SCENARIOS_SOURCE=files|database|hybrid; scenarios_publish, reload_scenarios.

Приёмка:
- check_in_three.yaml: greet → reflect → close (demo_turn --scenario check_in_three).
- branch_mood.yaml — ветвление по keyword.
- test_scenario_keyword.py, test_scenarios_goal3.py.

3.5. Инструменты (tools) v1
---------------------------
| Tool            | Назначение                          | Статус      |
|-----------------|-------------------------------------|-------------|
| memory_search   | Поиск в долгой памяти               | Готово      |
| memory_upsert   | Запись факта                        | Готово      |
| web_search      | Поиск в сети (WEB_SEARCH_URL)       | Код есть    |
| rag_search      | Методички центра                    | Не сделано  |

Цикл вызова:
- USE_LANGGRAPH=true — LangGraph llm ↔ tools;
- TEXT_TOOL_FALLBACK=true — Plan B, если модель не отдаёт tool_calls.

Приёмка с live LLM:
- live_acceptance: диалог с upsert/search в БД (блок 2.2 — ждёт API).

3.6. Модерация и лимиты
-----------------------
- blocked_input_substrings / blocked_output_substrings (moderation.yaml).
- MODERATION_ENABLED=true.
- Rate limit: RATE_LIMIT_PER_MINUTE, RATE_LIMIT_PER_HOUR.
- Лог security_incident + файл jsonl.

3.7. Логирование
----------------
Обязательные события на ход:
  gateway_in → modes_resolve → gateway_llm_engine → gateway_out

Поля (без ПДн по умолчанию):
  correlation_id, session_id, mode_id, scenario_id, scenario_node_id,
  latency_ms, modes_resolve_ms, memory_prefetch_ms, llm_ms,
  tool_calls, tool_rounds, reply_len

Файл: logs/agent.log (ротация по размеру в agent.yaml).
Эталон: docs/log_example_gateway.jsonl.

3.8. Отчёт для родителя (вне диалога)
-------------------------------------
CLI: parent_progress_report — выгрузка progress/note из БД без LLM.
Шаблон: docs/templates/parent_progress_ru.md.
Юрист: docs/pilot/MEMORY_FOR_LAWYER.md.

================================================================================
4. ТЕХНИЧЕСКИЙ СТЕК
================================================================================

- Python 3.11 или 3.12
- LangChain, LangGraph
- SQLAlchemy + aiosqlite (SQLite)
- Pydantic, pydantic-settings
- structlog (JSON-логи)
- OpenAI-compatible HTTP API (ChatOpenAI)

Структура пакета (кратко):
  src/center_voice_agent/
    agent/          — gateway, llm, tool_loop, prompt_builder
    orchestration/  — SessionCoordinator
    context/        — ShortTermMemory, session_messages
    memory/         — LongTermMemoryRepository
    modes/          — ModeRegistry, schema
    scenarios/      — graph_engine, loader, transitions
    tools/          — factory, impl (memory, web_search)
    security/       — moderation, rate_limit
    integration/    — bridge AgentSession для voice_assistant
    cli/            — init_db, demo_turn, live_turn, block2_offline, …
  config/           — modes, scenarios, voice, moderation, agent.yaml
  db/migrations/    — SQL миграции 001–005
  docs/             — документация и пилот
  tests/            — pytest

================================================================================
5. МОДЕЛЬ ДАННЫХ (SQLite)
================================================================================

Миграции: db/migrations/

001_init.sql:
  child_profiles
  long_term_memory_entries
  scenario_definitions (legacy/справочник)
  session_state

002_mode_definitions.sql:
  mode_definitions (id, config_yaml, …)

004_scenario_publish.sql:
  scenario_publish

005_session_messages.sql:
  session_messages (session_id, role, content_text, created_at)

Связь сессии и ребёнка: session_state.child_profile_id → child_profiles.id

================================================================================
6. КОНФИГУРАЦИЯ (.env и agent.yaml)
================================================================================

Секреты и URL (только .env, не коммитить):
  LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
  OPENAI_API_KEY (запасной)
  DATABASE_URL
  WEB_SEARCH_URL (опционально)

Поведение агента (.env / agent.yaml):
  SHORT_TERM_MAX_MESSAGES=15
  SHORT_TERM_SOURCE=memory|db
  PREFETCH_LONG_TERM_MEMORY=true
  PREFETCH_MEMORY_LIMIT=8
  USE_LANGGRAPH=true
  TEXT_TOOL_FALLBACK=true
  DEFAULT_MODE_ID=dialog
  MODES_SOURCE=files|hybrid
  SCENARIOS_SOURCE=files|hybrid
  MODERATION_ENABLED=true
  LOG_REDACT_USER_TEXT=true
  RATE_LIMIT_ENABLED=true

Логи (agent.yaml):
  log_file_path: logs/agent.log
  security_incidents_path: data/security_incidents.jsonl

================================================================================
7. ПРИЁМКА И КОМАНДЫ
================================================================================

7.1. Офлайн (без модели) — обязательный минимум перед пилотом
-----------------------------------------------------------
  cd center_voice_agent
  .\.venv\Scripts\activate
  pip install -e ".[dev]"
  python -m center_voice_agent.cli.init_db
  python -m center_voice_agent.cli.setup_check
  python -m center_voice_agent.cli.block2_offline
  python -m pytest tests/ -q
  python -m center_voice_agent.cli.demo_turn
  python -m center_voice_agent.cli.demo_turn --scenario check_in_three

7.2. С реальной моделью (блок 2.2)
----------------------------------
  Заполнить .env (ключ, URL вне restricted-региона или свой endpoint)
  python -m center_voice_agent.cli.live_turn "Привет!"
  python -m center_voice_agent.cli.live_acceptance

7.3. Текстовый пилот
--------------------
  scripts\start_pilot_text.bat
  или voice_assistant\voice_loop_text.py с USE_CENTER_AGENT=true

7.4. Критерий «первый рабочий день» (DECISIONS.md)
--------------------------------------------------
1. setup_check OK
2. live_acceptance OK (когда есть API)
3. В логах correlation_id, gateway_in, gateway_out
4. memory_upsert → search работает

================================================================================
8. ПИЛОТ С ДЕТЬМИ (ОРГАНИЗАЦИЯ)
================================================================================

Документы: docs/pilot/

  PASSPORT.md           — кто, где, сколько детей (ЗАПОЛНИТЬ)
  SUCCESS_CRITERIA.md — когда пилот успешен / стоп
  METRICS_FORM.md       — метрики
  MEMORY_FOR_LAWYER.md  — согласование памяти (юрист)
  DATA_RETENTION.md     — сроки хранения, purge_child
  PEDAGOG.md            — инструкция педагогу
  METHODIST_PILOT.md    — инструкция методисту
  ONCALL.md             — контакты при инциденте (ЗАПОЛНИТЬ)
  ROLLBACK.md           — откат версии/БД
  FEEDBACK.md           — обратная связь после пилота

Скрипты:
  scripts/start_pilot_text.bat
  scripts/pilot_backup_db.bat
  cli/purge_child.py — удаление данных ребёнка по запросу

================================================================================
9. ПЛАН РАБОТ ПО СПРИНТАМ (из WORK_PLAN.md)
================================================================================

S0 — Каркас репозитория                    [ВЫПОЛНЕНО]
  структура, pyproject, миграции, заглушки gateway, документация

S1 — Память                                 [ВЫПОЛНЕНО]
  short_term, long_term, repository, prefetch, session_messages

S2 — Режимы                                 [ВЫПОЛНЕНО]
  YAML, ModeRegistry, hybrid, calm, reload_modes

S3 — Сценарии                               [ВЫПОЛНЕНО]
  граф, LangGraph tool loop, keyword when, hybrid publish

S4 — Tools + live LLM                       [ЧАСТИЧНО]
  memory tools OK; live_turn ждёт API/регион

S5 — MCP                                    [НЕ СДЕЛАНО]
  mcp/server.py, паритет с LangChain tools

S6 — Голос E2E                              [ЧАСТИЧНО]
  bridge, voice_loop_text; ASR/TTS в GUI — нет

S7 — Модерация, нагрузка                    [ЧАСТИЧНО]
  модерация, rate limit OK; нагрузочные тесты — нет

Дополнительно (бэклог):
  Блок 11 — PostgreSQL, Redis, Docker, health
  Блок 7.6 — RAG (методички)
  Блок 3.1 — PR в master на GitHub
  Блок E — LLMProvider, schema_migrations, FastAPI /turn

================================================================================
10. ТЕКУЩИЙ СТАТУС ВЫПОЛНЕНИЯ (кратко)
================================================================================

Оценка готовности:
  Каркас агента (код без live API):     ~70–75%
  Полное ТЗ (LLM + голос + MCP + прод):  ~45–50%

Сделано в коде:
  Блоки 0, 1, 4, 5, 6, B, большая часть 9, часть 10, шаблоны 12.

Не сделано / блокеры:
  - live_turn / live_acceptance (API 403 регион или нет endpoint)
  - PR merge в master
  - Заполнение PASSPORT, ONCALL, юрист
  - MCP, RAG, PostgreSQL, полный голос E2E

Ветка GitHub: center-voice-agent (актуальный код)
Сравнение PR: docs/PR_CENTER_VOICE_AGENT.md

================================================================================
11. РИСКИ
================================================================================

- ПДн в логах — mitigated через LOG_REDACT_USER_TEXT.
- Модель без tool-calling — mitigated через TEXT_TOOL_FALLBACK.
- MCP на Windows — тестировать отдельно при внедрении.
- Один SQLite — бэкап перед пилотом (pilot_backup_db.bat).
- Несколько процессов агента — нужен общий DATABASE_URL или Redis (будущее).

================================================================================
12. КОНТАКТЫ И РЕШЕНИЯ НА KICKOFF (зафиксировать)
================================================================================

[ ] Формат TTS: одно поле reply_spoken или SSML
[ ] Хостинг LLM: URL, модель, регион
[ ] БД на проде: SQLite vs PostgreSQL
[ ] Юрист: whitelist памяти + срок хранения + отчёт родителям
[ ] Default branch на GitHub: center-voice-agent vs master

================================================================================
КОНЕЦ ДОКУМЕНТА
================================================================================
