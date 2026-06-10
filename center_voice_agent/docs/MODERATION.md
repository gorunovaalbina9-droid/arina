# Модерация и security_incident (блок B)

## Конфиг

`config/moderation.yaml`:

- `blocked_input_substrings` / `blocked_output_substrings` — подстроки (с нормализацией leet/пробелов)
- `blocked_input_patterns` / `blocked_output_patterns` — regex (`re.IGNORECASE`)
- `blocked_substrings` — устаревший общий список

Перезагрузка: перезапуск процесса (Settings читает YAML при старте).

Опционально внешний API: `MODERATION_API_URL` — POST `{"text","direction"}` → `{"blocked": true, "reason": "..."}`.

## Эскалация педагогу

После `MODERATION_ESCALATION_THRESHOLD` блокировок за час на одного ребёнка — событие `moderation_escalation` с `notify_pedagogue: true` в логах и `security_incidents.jsonl`.

## События в логах

| event | direction | Когда |
|-------|-----------|-------|
| `security_incident` | `input` / `output` | Модерация |
| `security_incident` | `rate_limit` | Лимит ходов |
| `security_incident` | `consent` | Нет согласия родителя |
| `moderation_escalation` | — | Порог блокировок |

Текст ребёнка: `LOG_REDACT_USER_TEXT=true` → только fingerprint в `gateway_in`.
Аргументы tools: `LOG_REDACT_TOOL_ARGS=true` → redact в `AgentTurnResult.tool_calls`.

## Rate limit

- `RATE_LIMIT_BACKEND=memory` — один процесс (по умолчанию)
- `RATE_LIMIT_BACKEND=redis` + `REDIS_URL` — shared между воркерами (`pip install center-voice-agent[redis]`)

## web_search

По умолчанию **выключен** (`WEB_SEARCH_ENABLED=false`). Убран из детских режимов в YAML. Для staff: включить env и `WEB_SEARCH_ALLOWED_MODE_IDS`.

## 152-ФЗ

См. [compliance/152FZ.md](compliance/152FZ.md): согласия, LLM region, retention.

## Отключение

`.env`: `MODERATION_ENABLED=false`, `RATE_LIMIT_ENABLED=false`.
