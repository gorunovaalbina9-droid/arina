# Методист: контент пилота (12.3.2)

База: [METHODIST.md](../METHODIST.md).

## Перед пилотом

| Шаг | Действие |
|-----|----------|
| 1 | Волна 1: режим `dialog` или сценарий `check_in_three` |
| 2 | В YAML режима на пилоте убрать `web_search` из `tool_ids` (рекомендуется) |
| 3 | Проверить фразы: коротко, без страха, без запроса адреса/телефона |
| 4 | `python -m center_voice_agent.cli.reload_modes` |
| 5 | Тест: `python -m center_voice_agent.cli.demo_turn` или `text_turn --live` |

## Файлы

- Режимы: `config/modes/*.yaml`  
- Сценарии: `config/scenarios/check_in_three.yaml`  
- Возраст: `config/age_bands/default.yaml`  
- Голосовые команды: `config/voice/mode_commands.yaml`

## Публикация в БД (опционально)

```bash
python -m center_voice_agent.cli.scenarios_publish config/scenarios/check_in_three.yaml
```

`.env`: `SCENARIOS_SOURCE=files` на пилоте проще.

## После пилота

Собрать правки YAML → commit в `center-voice-agent` или передать разработчику.
