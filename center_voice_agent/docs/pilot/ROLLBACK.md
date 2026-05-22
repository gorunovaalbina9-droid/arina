# План отката (12.5)

Стабильный коммит пилота: **`018ff24`** (или тег, который зафиксируете в [PASSPORT.md](PASSPORT.md)).

## Уровень 1 — конфиг (5 мин)

- Вернуть YAML: `git checkout <commit> -- config/modes/dialog.yaml` → `reload_modes`  
- Сценарий off: не вызывать `attach_scenario`  
- `.env`: `PREFETCH_LONG_TERM_MEMORY=false`

## Уровень 2 — код

```powershell
cd c:\Users\Альбина\глебебля2
git fetch origin
git checkout center-voice-agent
git checkout 018ff24 -- center_voice_agent/
cd center_voice_agent
.\.venv\Scripts\python.exe -m center_voice_agent.cli.setup_check
```

## Уровень 3 — БД

- Один ребёнок: `python -m center_voice_agent.cli.purge_child ID --confirm`  
- Вся БД: восстановить `data\agent.db` из бэкапа (`scripts\pilot_backup_db.bat`)

## Уровень 4 — полный стоп

Отключить агента в боте; занятие без робота по карточкам методиста.

## До пилота

Запускать `scripts\pilot_backup_db.bat` в конце каждого дня подготовки.
