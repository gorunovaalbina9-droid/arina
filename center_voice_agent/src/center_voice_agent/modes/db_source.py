from __future__ import annotations

import sqlite3
import uuid
from collections import defaultdict
from typing import Optional

from center_voice_agent.db.sqlite_path import sqlite_file_path_from_url


def fetch_published_mode_yamls(
    database_url: str,
    *,
    center_id: Optional[str] = None,
) -> dict[str, str]:
    """
    Синхронное чтение опубликованных режимов из SQLite.
    - Если center_id не задан: только строки с center_id IS NULL (глобальные).
    - Если задан: строки center_id = :cid или NULL; для одного mode_id приоритет у центра, иначе глобальная.
    """
    path = sqlite_file_path_from_url(database_url)
    if path is None or not path.is_file():
        return {}
    conn = sqlite3.connect(str(path))
    try:
        if center_id is None:
            cur = conn.execute(
                """
                SELECT mode_id, config_yaml, version
                FROM mode_definitions
                WHERE status = 'published' AND center_id IS NULL
                ORDER BY mode_id, version DESC
                """
            )
            rows = [(r[0], r[1], r[2], None) for r in cur.fetchall()]
        else:
            cur = conn.execute(
                """
                SELECT mode_id, config_yaml, version, center_id
                FROM mode_definitions
                WHERE status = 'published' AND (center_id IS NULL OR center_id = ?)
                ORDER BY mode_id, version DESC
                """,
                (center_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if center_id is None:
        out: dict[str, str] = {}
        for mode_id, yaml_text, _ver, _ in rows:
            if mode_id not in out:
                out[str(mode_id)] = str(yaml_text)
        return out

    buckets: dict[str, list[tuple[str, int, Optional[str]]]] = defaultdict(list)
    for mode_id, yaml_text, ver, cid in rows:
        buckets[str(mode_id)].append((str(yaml_text), int(ver), cid))

    out2: dict[str, str] = {}
    for mid, lst in buckets.items():
        lst.sort(
            key=lambda x: (
                0 if x[2] == center_id else 1 if x[2] is None else 2,
                -x[1],
            )
        )
        out2[mid] = lst[0][0]
    return out2


def publish_mode_yaml_sync(
    database_url: str,
    *,
    config_yaml: str,
    mode_id: str,
    center_id: Optional[str] = None,
    status: str = "published",
) -> str:
    """Записать определение режима в БД (черновик или опубликовано). Возвращает id строки."""
    path = sqlite_file_path_from_url(database_url)
    if path is None:
        raise ValueError("publish_mode_yaml_sync поддерживает только SQLite (sqlite+aiosqlite)")
    rid = str(uuid.uuid4())
    conn = sqlite3.connect(str(path))
    try:
        if status == "published":
            conn.execute(
                """
                DELETE FROM mode_definitions
                WHERE mode_id = ? AND status = 'published'
                  AND (center_id IS ? OR (center_id IS NULL AND ? IS NULL))
                """,
                (mode_id, center_id, center_id),
            )
        cur = conn.execute(
            "SELECT COALESCE(MAX(version), 0) + 1 FROM mode_definitions WHERE mode_id = ?",
            (mode_id,),
        )
        nxt = int(cur.fetchone()[0])
        conn.execute(
            """
            INSERT INTO mode_definitions (id, mode_id, center_id, status, version, config_yaml, updated_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (rid, mode_id, center_id, status, nxt, config_yaml),
        )
        conn.commit()
    finally:
        conn.close()
    return rid
