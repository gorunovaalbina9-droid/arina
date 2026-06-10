-- PostgreSQL: scenario_publish (004)

CREATE TABLE IF NOT EXISTS scenario_publish (
    id              TEXT PRIMARY KEY,
    scenario_id     TEXT NOT NULL,
    center_id       TEXT,
    status          TEXT NOT NULL DEFAULT 'draft',
    version         INTEGER NOT NULL DEFAULT 1,
    config_yaml     TEXT NOT NULL,
    subject         TEXT,
    age_band        TEXT,
    created_at      TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
    updated_at      TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
);

CREATE INDEX IF NOT EXISTS idx_scenario_pub_scenario_status ON scenario_publish(scenario_id, status);
