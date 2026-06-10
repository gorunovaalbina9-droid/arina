# Alembic для PostgreSQL (дополнение к SQL-миграциям)

[Alembic](https://alembic.sqlalchemy.org/) используется для **инкрементальных** изменений схемы
в проде на PostgreSQL. Начальная схема по-прежнему создаётся SQL-файлами в
`db/migrations/postgresql/` через `center-agent-init-db`.

## Быстрый старт

```bash
pip install center-voice-agent[postgres,alembic]
export DATABASE_URL=postgresql+psycopg://user:pass@localhost/center_agent
alembic -c alembic.ini stamp head   # если SQL-миграции уже применены
alembic -c alembic.ini revision -m "add_example" --autogenerate
alembic -c alembic.ini upgrade head
```

## Связь с `schema_migrations`

| Механизм | Назначение |
|----------|------------|
| `db/migrations/postgresql/*.sql` | Bootstrap, пилот, CI |
| `alembic/versions/*.py` | Дальнейшие DDL в проде |

Baseline-ревизия `001_baseline` — пустой `upgrade()`; схема = результат SQL 001–006.
После `center-agent-init-db` выполните `alembic stamp head`.

## SQLite

Для локальной разработки достаточно `db/migrations/sqlite/`. Alembic на SQLite не обязателен.
