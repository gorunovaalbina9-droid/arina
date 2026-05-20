# Блок 2 — приёмка «первый реальный LLM»

Краткий чеклист. Подробности: [LIVE_LLM_ACCEPTANCE.md](LIVE_LLM_ACCEPTANCE.md).

## Подготовка

- [ ] Python 3.11/3.12, venv, `pip install -e ".[dev]"`
- [ ] `copy .env.example .env` — ключи **не** в git (`.env` в `.gitignore`)
- [ ] `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` — не `replace_me` / `example.com`
- [ ] `python -m center_voice_agent.cli.init_db`

## Запуск приёмки

```powershell
cd center_voice_agent
.\.venv\Scripts\activate
python -m center_voice_agent.cli.live_acceptance
```

Только проверка `.env` (без API):

```powershell
python -m center_voice_agent.cli.live_acceptance --dry-run
```

## Что должно пройти

| Шаг | Критерий |
|-----|----------|
| 2.1 | `.env` найден, LLM настроен |
| 2.2 | Ответ от реального API (не `StaticChatModel`) |
| 2.3 | `memory_upsert` → запись в SQLite → `memory_search` / маркер в ответе |
| 2.4 | В логах `correlation_id`, `gateway_in`, `gateway_out`; пример в `log_example_gateway.jsonl` |
| 2.5 | Отчёт: нативные tools или plan B (`TEXT_TOOL_FALLBACK`) |

## Дополнительно

```powershell
python -m center_voice_agent.cli.live_turn Привет!
python -m center_voice_agent.cli.text_turn --live
python -m center_voice_agent.cli.demo_turn --live
python -m pytest tests/test_text_tool_fallback.py -q
```
