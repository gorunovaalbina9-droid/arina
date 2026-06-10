# Хранение и удаление ПДн (12.2.2)

Заполните юридические поля с DPO центра. Техническая реализация — ниже.

## Политика (значения по умолчанию в коде)

| Вопрос | Env / код | Значение по умолчанию |
|--------|-----------|------------------------|
| Срок `session_messages` | `SESSION_MESSAGES_RETENTION_DAYS` | 90 дней |
| Срок `session_state` | `SESSION_STATE_RETENTION_DAYS` | 180 дней |
| Ротация agent.log | `LOG_FILE_MAX_BYTES`, `LOG_FILE_BACKUP_COUNT` | 5 MB, 3 файла |
| Инциденты модерации | `SECURITY_INCIDENTS_MAX_BYTES` | 1 MB (trim) |
| Авто-purge при старте API/voice | `RETENTION_PURGE_ON_STARTUP` | false |

## CLI retention

```powershell
center-agent-retention-purge
center-agent-retention-purge --messages-days 60 --state-days 120
```

Удаляет строки старше порога из `session_messages` и `session_state`.

## Удаление данных ребёнка

```powershell
center-agent-purge-child CHILD_ID --confirm
```

Удаляет: `long_term_memory_entries`, `session_state`, `child_profiles` (CASCADE).

## Redact в логах

- `LOG_REDACT_USER_TEXT=true` — не логировать текст ребёнка целиком
- `LOG_REDACT_TOOL_ARGS=true` — маскировать аргументы tools (ПДн)

## До пилота

- [ ] Согласовать сроки с [152FZ.md](../compliance/152FZ.md)
- [ ] Включить `RETENTION_PURGE_ON_STARTUP=true` на prod или cron `center-agent-retention-purge`
- [ ] Репетиция: `center-agent-create-child` → `center-agent-memory-roundtrip` → `center-agent-purge-child --confirm`
