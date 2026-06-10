-- 003: учёт версий миграций (не пропуск в нумерации — см. migrations/README.md).
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     TEXT PRIMARY KEY,
    applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
