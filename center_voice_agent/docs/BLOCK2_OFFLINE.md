# Блок 2 без готовой модели

Пока нет дообученной модели и ключа API, закрывается **офлайн-часть** блока 2.

## Одна команда

```powershell
cd center_voice_agent
.\.venv\Scripts\activate
python -m center_voice_agent.cli.block2_offline
```

## Что проверяется без API

| ID | Задача | Как |
|----|--------|-----|
| 2.3 | Память upsert → SQLite → search | Внутри `block2_offline` |
| 2.4 | Формат логов | `demo_turn` с fake LLM + `log_example_gateway.jsonl` |
| 2.5 | Plan B | Код `text_tool_fallback.py`, флаг в Settings |
| — | БД, режимы | `init_db`, `ModeRegistry` |

## Что остаётся после появления модели

```powershell
copy .env.example .env
# заполнить LLM_* 
python -m center_voice_agent.cli.setup_check
python -m center_voice_agent.cli.live_turn "Привет!"
python -m center_voice_agent.cli.live_acceptance
```

См. [LIVE_LLM_ACCEPTANCE.md](LIVE_LLM_ACCEPTANCE.md).
