# С чего начать (center_voice_agent)

**Вы — здесь.** Остальное делает код; вам нужны ключ API и 30–60 минут по чеклисту.

## Шаг 1. Python 3.12

```powershell
cd center_voice_agent
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
```

## Шаг 2. Настройки

```powershell
copy .env.example .env
notepad .env
```

Заполните минимум:

- `LLM_API_KEY` — ваш ключ  
- `LLM_BASE_URL` — адрес API (как OpenAI)  
- `LLM_MODEL` — имя модели  

## Шаг 3. Проверка

```powershell
python -m center_voice_agent.cli.setup_check
python -m center_voice_agent.cli.demo_turn
python -m pytest tests/ -q
```

## Шаг 4. Реальная модель

```powershell
python -m center_voice_agent.cli.live_turn Привет!
```

## Дальше

Подробная инструкция для вас: **[docs/INSTRUKCIYA_DLYA_VAS.md](docs/INSTRUKCIYA_DLYA_VAS.md)**
