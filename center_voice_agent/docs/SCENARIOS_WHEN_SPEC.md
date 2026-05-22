# Условия переходов when (6.7)

Порядок в YAML: **первое совпадение**.

## Типы

| when | Когда проверяется | Текст |
|------|-------------------|-------|
| `turn_complete` | После ответа ассистента | — |
| `user_spoke` | Алиас к `turn_complete` | — |
| `always` | С событием turn_complete | — |
| `keyword:а,б,в` | **До** LLM, по реплике ребёнка | подстрока в lower |

## Пример

`config/scenarios/branch_mood.yaml`

## Логи

`scenario_transition` с полем `trigger`: `user_keyword` | `turn_complete`.
