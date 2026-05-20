# Чеклист мелких целей

Отмечайте `[x]` по мере выполнения. См. [DECISIONS.md](DECISIONS.md).

## Блок 0 — сделано в коде

- [x] 0.1–0.14 Каркас, память, режимы, сценарии, LangGraph, тесты

## Блок 1 — организация

- [x] 1.1 DECISIONS.md
- [x] 1.2 Python 3.11/3.12 (.python-version, README)
- [x] 1.3 LLM в DECISIONS
- [x] 1.4 Критерий первого рабочего дня
- [x] 1.5 Чеклист быстрого старта в README

## Блок 2 — реальный LLM

- [x] 2.1 Ключ подхватывается (`LLM_*` или `OPENAI_API_KEY` из `voice_assistant/.env`)
- [ ] 2.2 `cli.live_acceptance` / `live_turn` — нужен **баланс** на API (сейчас 429 quota)
- [x] 2.3 `cli.memory_roundtrip` — upsert→SQLite→search OK
- [x] 2.4 Формат логов `correlation_id`, `gateway_in`/`gateway_out` (см. `log_example_gateway.jsonl`)
- [x] 2.5 План B tool-calling (`TEXT_TOOL_FALLBACK`, `text_tool_fallback.py`)

## Блок 3 — Git

- [ ] 3.1 PR center-voice-agent → master
- [x] 3.2 Ветка в README
- [x] 3.3 .gitignore больших артефактов
- [ ] 3.4 Очистка истории master от >100 MB

## Блок 4 — память

- [x] 4.1 PREFETCH_LONG_TERM_MEMORY
- [x] 4.2 LOG_REDACT_USER_TEXT
- [x] 4.3 MEMORY_CATEGORIES.md
- [ ] 4.4 session_messages (опционально)

## Блок 5 — режимы

- [x] 5.1 METHODIST.md
- [ ] 5.2 Стенд hybrid + modes_publish
- [ ] 5.3 Hot-reload API
- [ ] 5.4 Четвёртый режим от методиста

## Блок 6 — сценарии

- [x] 6.1 check_in_three.yaml
- [x] 6.3–6.4 Тесты 3 узла и сброс
- [ ] 6.5 Стенд SCENARIOS hybrid
- [x] 6.6 Дока scenario_publish vs scenario_definitions
- [ ] 6.7 keyword when
- [ ] 6.8 advance в LangGraph

## Блок 7 — tools

- [x] 7.1 tools/impl/
- [x] 7.2–7.5 web_search + лимиты
- [ ] 7.6–7.7 rag_search

## Блок 8 — MCP

- [ ] 8.1–8.5 MCP server

## Блок 9 — логи

- [x] 9.2 correlation_id
- [x] 9.5 security_incident заглушка
- [ ] 9.1 ротация файлов
- [ ] 9.3 latency по этапам
- [ ] 9.4 LangSmith

## Блок 10 — голос

- [x] 10.1–10.2 reply_spoken
- [x] 10.3 INTEGRATION.md
- [x] 10.4 text_turn CLI
- [ ] 10.5–10.7 ASR/TTS E2E

## Блок 11 — прод

- [x] 11.1 create_child CLI
- [ ] 11.2–11.7 PG, Redis, нагрузка

## Блок 12 — пилот

- [ ] 12.1–12.6
