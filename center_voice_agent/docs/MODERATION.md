# Модерация и security_incident (блок B)

## Конфиг

`config/moderation.yaml`:

- `blocked_input_substrings` — до вызова LLM (реплика ребёнка)
- `blocked_output_substrings` — после ответа модели
- `blocked_substrings` — устаревший общий список (дублируется в оба, если split пуст)

Перезагрузка: перезапуск процесса (Settings читает YAML при старте).

## События в логах

| event | direction | Когда | Поля |
|-------|-----------|-------|------|
| `security_incident` | `input` | Заблокирован запрос | `reason` (напр. `blocked_phrase:…`), `session_id`, `child_profile_id` |
| `security_incident` | `output` | Подменён ответ модели | то же |
| `security_incident` | `rate_limit` | Слишком много ходов | `reason` `rate_limit:minute:…` |
| `security_incident` | `tool` | LLM передал чужой `child_profile_id` в tool | `attempted_child_profile_id`, `tool` |

Текст ребёнка в логах: при `LOG_REDACT_USER_TEXT=true` в `gateway_in` только `user_text_fp`, не полный текст.

## Поведение

- **Вход:** ответ «Давай поговорим о чём-нибудь другом…», LLM не вызывается.
- **Выход:** «Извини, я не могу так ответить…»
- **Rate limit:** «Подожди немного…» (по умолчанию 20/мин, 120/час на `session_id`).
- **Память:** `child_profile_id` в args tools игнорируется; подмена логируется.

## On-call

См. [pilot/ONCALL.md](pilot/ONCALL.md): L2 = модерация, L3 = ответ мимо списка.

## Отключение

`.env`: `MODERATION_ENABLED=false`, `RATE_LIMIT_ENABLED=false`.
