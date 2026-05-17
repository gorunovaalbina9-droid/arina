from __future__ import annotations

import sqlite3
import uuid
from collections import defaultdict
from typing import Optional

from center_voice_agent.db.sqlite_path import sqlite_file_path_from_url


def fetch_published_scenario_yamls(
    database_url: str,
    *,
    center_id: Optional[str] = None,
) -> dict[str, str]:
    """Опубликованные YAML графов сценариев (ключ — поле id внутри YAML)."""
    path = sqlite_file_path_from_url(database_url)
    if path is None or not path.is_file():
        return {}
    conn = sqlite3.connect(str(path))
    try:
        if center_id is None:
            cur = conn.execute(
                """
                SELECT scenario_id, config_yaml, version
                FROM scenario_publish
                WHERE status = 'published' AND center_id IS NULL
                ORDER BY scenario_id, version DESC
                """
            )
            rows = [(r[0], r[1], r[2], None) for r in cur.fetchall()]
        else:
            cur = conn.execute(
                """
                SELECT scenario_id, config_yaml, version, center_id
                FROM scenario_publish
                WHERE status = 'published' AND (center_id IS NULL OR center_id = ?)
                ORDER BY scenario_id, version DESC
                """,
                (center_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if center_id is None:
        out: dict[str, str] = {}
        for scenario_id, yaml_text, _ver, _ in rows:
            if scenario_id not in out:
                out[str(scenario_id)] = str(yaml_text)
        return out

    buckets: dict[str, list[tuple[str, int, Optional[str]]]] = defaultdict(list)
    for scenario_id, yaml_text, ver, cid in rows:
        buckets[str(scenario_id)].append((str(yaml_text), int(ver), cid))

    out2: dict[str, str] = {}
    for sid, lst in buckets.items():
        lst.sort(
            key=lambda x: (
                0 if x[2] == center_id else 1 if x[2] is None else 2,
                -x[1],
            )
        )
        out2[sid] = lst[0][0]
    return out2


def publish_scenario_yaml_sync(
    database_url: str,
    *,
    config_yaml: str,
    scenario_id: str,
    center_id: Optional[str] = None,
    status: str = "published",
    subject: Optional[str] = None,
    age_band: Optional[str] = None,
) -> str:
    path = sqlite_file_path_from_url(database_url)
    if path is None:
        raise ValueError("publish_scenario_yaml_sync поддерживает только SQLite (sqlite+aiosqlite)")
    rid = str(uuid.uuid4())
    conn = sqlite3.connect(str(path))
    try:
        if status == "published":
            conn.execute(
                """
                DELETE FROM scenario_publish
                WHERE scenario_id = ? AND status = 'published'
                  AND (center_id IS ? OR (center_id IS NULL AND ? IS NULL))
                """,
                (scenario_id, center_id, center_id),
            )
        cur = conn.execute(
            "SELECT COALESCE(MAX(version), 0) + 1 FROM scenario_publish WHERE scenario_id = ?",
            (scenario_id,),
        )
        nxt = int(cur.fetchone()[0])
        conn.execute(
            """
            INSERT INTO scenario_publish (
                id, scenario_id, center_id, status, version, config_yaml,
                subject, age_band, updated_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (rid, scenario_id, center_id, status, nxt, config_yaml, subject, age_band),
        )
        conn.commit()
    finally:
        conn.close()
    return rid
