# Инструкция методисту: режимы и сценарии

## Новый режим (без программиста)

1. Создайте файл `config/modes/my_mode.yaml` (латиница, `id` в snake_case).
2. Обязательно: `id`, `display_name`, `system_prompt` или `system_prompt_path`, `tool_ids` (можно `[]`).
3. Опционально: `allowed_transitions`, `voice_aliases`, `llm_params`, `max_tool_rounds`.
4. Проверка: `python -m center_voice_agent.cli.reload_modes`.

Пример минимального режима:

```yaml
id: calm
display_name: Спокойный диалог
system_prompt: |
  Ты спокойный наставник. Короткие фразы, без сложных терминов.
tool_ids: []
allowed_transitions: [dialog, lesson]
```

## Новый сценарий

1. Файл `config/scenarios/my_story.yaml` с полями `id`, `entry`, `nodes`.
2. У каждого узла: `title`, `prompt_to_model`, `transitions` (или пусто на финале).
3. Переход после ответа ассистента: `when: turn_complete` → `next: other_node_id`.
4. Привязка к сессии: `attach_scenario(session_id, scenario_id)` в коде интеграции или через ваш бот.

Публикация в БД (без деплоя файла):

```bash
python -m center_voice_agent.cli.scenarios_publish config/scenarios/my_story.yaml
```

В `.env`: `SCENARIOS_SOURCE=hybrid`.

## Голосовые фразы

- Смена режима: `config/voice/mode_commands.yaml` + `voice_aliases` в YAML режима.
- Сброс сценария: `config/voice/scenario_commands.yaml` (`reset_phrases`).
