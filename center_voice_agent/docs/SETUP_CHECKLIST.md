# Чеклист: поднять стенд за 1–2 часа

Отметьте пункты по порядку. Договорённости — в [DECISIONS.md](DECISIONS.md).

## Окружение

- [ ] Установлен **Python 3.11 или 3.12** (`py -3.12 --version` или `python3.12 --version`)
- [ ] Клонирован репозиторий, открыта папка `center_voice_agent/`
- [ ] Создан venv: `py -3.12 -m venv .venv`
- [ ] Активирован venv (Windows: `.venv\Scripts\activate`)
- [ ] `pip install -e ".[dev]"` завершился без ошибок

## Конфигурация

- [ ] Скопирован `.env.example` → `.env`
- [ ] В `.env` задан `DATABASE_URL` (можно оставить SQLite из примера)
- [ ] Для демо без API: можно не заполнять `LLM_API_KEY` (используется `demo_turn`)
- [ ] Для реального LLM: заполнены `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`

## Проверка

- [ ] `python -m center_voice_agent.cli.init_db` — OK
- [ ] `python -m center_voice_agent.cli.reload_modes` — строка `OK: dialog, lesson, ...`
- [ ] `python -m center_voice_agent.cli.demo_turn` — логи `gateway_in` / `gateway_out`
- [ ] `python -m pytest tests/ -q` — все тесты зелёные

## Первый рабочий день (с реальным API)

- [ ] `python -m center_voice_agent.cli.live_turn Привет!` — ответ от модели
- [ ] В логах есть `correlation_id`
- [ ] (Опционально) режим с `memory_*` tools — факт в SQLite после tool

**Приёмка блока 1:** все пункты «Окружение» и «Проверка» отмечены; при необходимости — пункты «Первый рабочий день».
