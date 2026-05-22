-- Краткосрочная память диалога (последние N реплик на session_id)

CREATE TABLE IF NOT EXISTS session_messages (
    id              TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL REFERENCES session_state(session_id) ON DELETE CASCADE,
    role            TEXT NOT NULL,
    content_text    TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_session_messages_sid_time
    ON session_messages(session_id, created_at);
