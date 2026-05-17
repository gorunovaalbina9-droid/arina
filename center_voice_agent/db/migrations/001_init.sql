-- Оболочка профиля + долгосрочная память (без UI профиля в этом репозитории)
-- SQLite-compatible schema. For PostgreSQL adjust types if needed.

CREATE TABLE IF NOT EXISTS child_profiles (
    id              TEXT PRIMARY KEY,
    center_id       TEXT NOT NULL,
    display_name    TEXT,
    age_band        TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    meta_json       TEXT
);

CREATE TABLE IF NOT EXISTS long_term_memory_entries (
    id              TEXT PRIMARY KEY,
    child_profile_id TEXT NOT NULL REFERENCES child_profiles(id) ON DELETE CASCADE,
    category        TEXT NOT NULL,
    key             TEXT,
    value_text      TEXT NOT NULL,
    source          TEXT NOT NULL DEFAULT 'agent',
    confidence      REAL,
    valid_from      TEXT,
    valid_until     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ltm_child ON long_term_memory_entries(child_profile_id);
CREATE INDEX IF NOT EXISTS idx_ltm_category ON long_term_memory_entries(child_profile_id, category);

CREATE TABLE IF NOT EXISTS scenario_definitions (
    id              TEXT PRIMARY KEY,
    subject         TEXT NOT NULL,
    age_band        TEXT,
    version         INTEGER NOT NULL DEFAULT 1,
    status          TEXT NOT NULL DEFAULT 'draft',
    graph_yaml_path TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS session_state (
    session_id      TEXT PRIMARY KEY,
    child_profile_id TEXT NOT NULL,
    mode_id         TEXT NOT NULL,
    scenario_id     TEXT,
    scenario_node_id TEXT,
    state_json      TEXT NOT NULL,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
