-- Режимы из БД (публикация из админки / CLI). Файлы в config/modes остаются fallback и базой для hybrid.

CREATE TABLE IF NOT EXISTS mode_definitions (
    id              TEXT PRIMARY KEY,
    mode_id         TEXT NOT NULL,
    center_id       TEXT,
    status          TEXT NOT NULL DEFAULT 'draft',
    version         INTEGER NOT NULL DEFAULT 1,
    config_yaml     TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_mode_def_mode_status ON mode_definitions(mode_id, status);
