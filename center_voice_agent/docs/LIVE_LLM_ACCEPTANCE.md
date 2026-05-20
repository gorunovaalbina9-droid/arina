# Приёмка: первый реальный LLM (блок 2)

## Что сделать вам

1. В `center_voice_agent/.env` (не в git):
   - `LLM_API_KEY=...`
   - `LLM_BASE_URL=...` (OpenAI-compatible)
   - `LLM_MODEL=...` (лучше модель с **tool-calling**, например `gpt-4o-mini`)

2. Запуск:

```powershell
cd center_voice_agent
.\.venv\Scripts\activate
python -m center_voice_agent.cli.live_acceptance
```

Проверка только `.env` без API:

```powershell
python -m center_voice_agent.cli.live_acceptance --dry-run
```

## Что проверяет скрипт

| Шаг | Проверка |
|-----|----------|
| 2.1 | `.env` есть, ключи не заглушки, не в git |
| 2.2 | 1+ реплики через **реальный** ChatOpenAI (не `StaticChatModel`) |
| 2.3 | `memory_upsert` → запись в SQLite → `memory_search` / текст с маркером |
| 2.4 | В консоли JSON: `correlation_id`, `gateway_in`, `gateway_out` |
| 2.5 | Если модель не зовёт tools — **plan B**: `TEXT_TOOL_FALLBACK=true` (по умолчанию) |

## План B (модель без tool-calling)

В ответе модель может написать JSON:

```json
{"tool": "memory_upsert", "args": {"category": "hobby", "value_text": "любит лего", "child_profile_id": "child-..."}}
```

Шлюз распознает это (`gateway_text_tool_fallback` в логах) и выполнит инструмент.

Отключить: `TEXT_TOOL_FALLBACK=false` в `.env`.

Подробнее: [DECISIONS.md](DECISIONS.md).

## Пример логов

См. [log_example_gateway.jsonl](log_example_gateway.jsonl).

## Если OpenAI отвечает 429 (нет баланса)

Пополните счёт или смените `LLM_BASE_URL` / ключ. Память без нейросети:

```powershell
python -m center_voice_agent.cli.memory_roundtrip
```

## Другие команды

```powershell
python -m center_voice_agent.cli.live_turn Привет!
python -m center_voice_agent.cli.demo_turn --live
python -m center_voice_agent.cli.text_turn --live
```
