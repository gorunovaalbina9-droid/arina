# Миграции БД

Версионирование через таблицу `schema_migrations` (создаётся ранner'ом до применения файлов).

## Каталоги

| Каталог | Движок |
|---------|--------|
| `sqlite/` | SQLite (`sqlite+aiosqlite:///...`) — разработка и пилот |
| `postgresql/` | PostgreSQL (`postgresql+asyncpg://...`) — прод |

Runner: `center_voice_agent.db.migrations_runner.run_migrations` — только **неприменённые** файлы, разбор SQL без наивного `split(';')`.

## Нумерация файлов

| Файл | Назначение |
|------|------------|
| `001_init` | child_profiles, LTM, session_state, legacy scenario_definitions |
| `002_mode_definitions` | Публикация режимов |
| **`003_schema_migrations`** | Таблица учёта версий (дублирует bootstrap runner'а, idempotent) |
| `004_scenario_publish` | Публикация сценариев |
| `005_session_messages` | STM в БД |
| `006_scenario_definitions_legacy` | Переименование устаревшей таблицы |

**003 не «пропущен»** — это отдельный шаг учёта миграций между доменными DDL.

## Применение

```bash
center-agent-init-db   # init_database → run_migrations
```

Повторный вызов безопасен: применяются только новые `NNN_*.sql`.

## Legacy БД

Если `session_state` уже есть, а `schema_migrations` пуста — runner помечает 001–005 (и 003) как применённые, затем выполнит только 006 и новее.

## PostgreSQL

Используйте URL `postgresql+asyncpg://user:pass@host/db` и каталог `postgresql/`. Для async нужен пакет `asyncpg` (опционально в pyproject).

Файлы в корне `migrations/*.sql` (без подкаталога) — **устарели**, оставлены только как fallback; предпочтительно `sqlite/` или `postgresql/`.
