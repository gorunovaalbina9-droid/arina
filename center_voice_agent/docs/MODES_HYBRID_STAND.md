# Стенд MODES_SOURCE=hybrid (5.2)

Файлы на диске + опубликованные версии в SQLite поверх них.

## Подготовка

```powershell
cd center_voice_agent
.\.venv\Scripts\activate
copy .env.example .env
# в .env:
# MODES_SOURCE=hybrid
# DATABASE_URL=sqlite+aiosqlite:///./data/agent.db
python -m center_voice_agent.cli.init_db
```

## Шаг 1 — publish

```powershell
python -m center_voice_agent.cli.modes_publish config\modes\lesson.yaml
# опционально привязка к центру:
python -m center_voice_agent.cli.modes_publish config\modes\lesson.yaml --center-id default-center
```

Ожидание: `OK row_id=... mode_id=lesson status=published`.

## Шаг 2 — reload

```powershell
python -m center_voice_agent.cli.reload_modes
```

Ожидание: `OK: dialog, lesson, play` (и `calm`, если добавлен).

В JSON-логе: `mode_registry_loaded`, поле `database_mode_ids` содержит `lesson`.

## Шаг 3 — проверка overlay

1. Временно измените `system_prompt` в publish (отдельный YAML) и снова `modes_publish`.
2. `reload_modes`.
3. `python -m center_voice_agent.cli.demo_turn` — в логе `modes_resolve` режим `lesson` с текстом из БД.

Автотест: `pytest tests/test_hybrid_sources.py::test_modes_hybrid_overlay -q`

## Long-running бот

Отдельный `reload_modes` **не** обновляет уже запущенный процесс. См. [MODES_RELOAD.md](MODES_RELOAD.md).

## Откат

- Republish старого YAML из `config/modes/`, или
- Удалить строку в `mode_definitions`, `reload_modes`.

Чеклист: [MODES_HYBRID_CHECKLIST.md](MODES_HYBRID_CHECKLIST.md).
