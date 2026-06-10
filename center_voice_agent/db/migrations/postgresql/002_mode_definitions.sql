-- PostgreSQL: mode_definitions (002)

CREATE TABLE IF NOT EXISTS mode_definitions (
    id              TEXT PRIMARY KEY,
    mode_id         TEXT NOT NULL,
    center_id       TEXT,
    status          TEXT NOT NULL DEFAULT 'draft',
    version         INTEGER NOT NULL DEFAULT 1,
    config_yaml     TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
    updated_at      TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);

CREATE INDEX IF NOT EXISTS idx_mode_def_mode_status ON mode_definitions(mode_id, status);
