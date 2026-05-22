# Отчёт «прогресс» для родителя (вне агента)

Агент **не** формирует отчёт сам. Накопление — через `memory_upsert` в категориях `progress` и `note` (см. [MEMORY_CATEGORIES.md](MEMORY_CATEGORIES.md)).

## CLI

```bash
python -m center_voice_agent.cli.parent_progress_report --child-profile-id child-1
python -m center_voice_agent.cli.parent_progress_report --child-profile-id child-1 --format json --out report.json
```

Или: `center-agent-parent-progress --child-profile-id child-1`

## Что входит

- Записи `progress` и `note` из `long_term_memory_entries`.
- Опционально: последний `scenario_id` / `scenario_node_id` из `session_state`.

## Что не входит

- Сырой текст диалога (`session_messages`).
- ПДн без согласования (адрес, телефон, диагнозы).

## Юридическая рамка

Перед рассылкой родителям — согласование шаблона с юристом ([pilot/MEMORY_FOR_LAWYER.md](pilot/MEMORY_FOR_LAWYER.md)).

## Шаблон для редактирования

См. [templates/parent_progress_ru.md](templates/parent_progress_ru.md).
