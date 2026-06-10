"""Чтение опубликованных режимов/сценариев — единая логика async + sync SQLAlchemy."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine


def _to_sync_database_url(database_url: str) -> str:
    if database_url.startswith("sqlite+aiosqlite:///"):
        return "sqlite:///" + database_url[len("sqlite+aiosqlite:///") :]
    return database_url


def _pick_mode_rows(
    rows: list[tuple[Any, ...]],
    *,
    center_id: Optional[str],
) -> dict[str, str]:
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


def _pick_scenario_rows(
    rows: list[tuple[Any, ...]],
    *,
    center_id: Optional[str],
) -> dict[str, str]:
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


async def _fetch_mode_rows_async(
    conn: AsyncConnection,
    *,
    center_id: Optional[str],
) -> list[tuple[Any, ...]]:
    if center_id is None:
        cur = await conn.execute(
            text(
                """
                SELECT mode_id, config_yaml, version
                FROM mode_definitions
                WHERE status = 'published' AND center_id IS NULL
                ORDER BY mode_id, version DESC
                """
            )
        )
        return [(r[0], r[1], r[2], None) for r in cur.fetchall()]

    cur = await conn.execute(
        text(
            """
            SELECT mode_id, config_yaml, version, center_id
            FROM mode_definitions
            WHERE status = 'published' AND (center_id IS NULL OR center_id = :cid)
            ORDER BY mode_id, version DESC
            """
        ),
        {"cid": center_id},
    )
    return cur.fetchall()


async def _fetch_scenario_rows_async(
    conn: AsyncConnection,
    *,
    center_id: Optional[str],
) -> list[tuple[Any, ...]]:
    if center_id is None:
        cur = await conn.execute(
            text(
                """
                SELECT scenario_id, config_yaml, version
                FROM scenario_publish
                WHERE status = 'published' AND center_id IS NULL
                ORDER BY scenario_id, version DESC
                """
            )
        )
        return [(r[0], r[1], r[2], None) for r in cur.fetchall()]

    cur = await conn.execute(
        text(
            """
            SELECT scenario_id, config_yaml, version, center_id
            FROM scenario_publish
            WHERE status = 'published' AND (center_id IS NULL OR center_id = :cid)
            ORDER BY scenario_id, version DESC
            """
        ),
        {"cid": center_id},
    )
    return cur.fetchall()


def _fetch_mode_rows_sync(
    conn: Connection,
    *,
    center_id: Optional[str],
) -> list[tuple[Any, ...]]:
    if center_id is None:
        cur = conn.execute(
            text(
                """
                SELECT mode_id, config_yaml, version
                FROM mode_definitions
                WHERE status = 'published' AND center_id IS NULL
                ORDER BY mode_id, version DESC
                """
            )
        )
        return [(r[0], r[1], r[2], None) for r in cur.fetchall()]

    cur = conn.execute(
        text(
            """
            SELECT mode_id, config_yaml, version, center_id
            FROM mode_definitions
            WHERE status = 'published' AND (center_id IS NULL OR center_id = :cid)
            ORDER BY mode_id, version DESC
            """
        ),
        {"cid": center_id},
    )
    return cur.fetchall()


def _fetch_scenario_rows_sync(
    conn: Connection,
    *,
    center_id: Optional[str],
) -> list[tuple[Any, ...]]:
    if center_id is None:
        cur = conn.execute(
            text(
                """
                SELECT scenario_id, config_yaml, version
                FROM scenario_publish
                WHERE status = 'published' AND center_id IS NULL
                ORDER BY scenario_id, version DESC
                """
            )
        )
        return [(r[0], r[1], r[2], None) for r in cur.fetchall()]

    cur = conn.execute(
        text(
            """
            SELECT scenario_id, config_yaml, version, center_id
            FROM scenario_publish
            WHERE status = 'published' AND (center_id IS NULL OR center_id = :cid)
            ORDER BY scenario_id, version DESC
            """
        ),
        {"cid": center_id},
    )
    return cur.fetchall()


async def fetch_published_mode_yamls_async(
    engine: AsyncEngine,
    *,
    center_id: Optional[str] = None,
) -> dict[str, str]:
    async with engine.connect() as conn:
        rows = await _fetch_mode_rows_async(conn, center_id=center_id)
    return _pick_mode_rows(rows, center_id=center_id)


async def fetch_published_scenario_yamls_async(
    engine: AsyncEngine,
    *,
    center_id: Optional[str] = None,
) -> dict[str, str]:
    async with engine.connect() as conn:
        rows = await _fetch_scenario_rows_async(conn, center_id=center_id)
    return _pick_scenario_rows(rows, center_id=center_id)


def fetch_published_mode_yamls_sync(
    database_url: str,
    *,
    center_id: Optional[str] = None,
) -> dict[str, str]:
    from sqlalchemy import create_engine

    from center_voice_agent.db.sqlite_path import sqlite_file_path_from_url

    path = sqlite_file_path_from_url(database_url)
    if path is None or not path.is_file():
        return {}
    eng = create_engine(_to_sync_database_url(database_url))
    try:
        with eng.connect() as conn:
            rows = _fetch_mode_rows_sync(conn, center_id=center_id)
        return _pick_mode_rows(rows, center_id=center_id)
    finally:
        eng.dispose()


def fetch_published_scenario_yamls_sync(
    database_url: str,
    *,
    center_id: Optional[str] = None,
) -> dict[str, str]:
    from sqlalchemy import create_engine

    from center_voice_agent.db.sqlite_path import sqlite_file_path_from_url

    path = sqlite_file_path_from_url(database_url)
    if path is None or not path.is_file():
        return {}
    eng = create_engine(_to_sync_database_url(database_url))
    try:
        with eng.connect() as conn:
            rows = _fetch_scenario_rows_sync(conn, center_id=center_id)
        return _pick_scenario_rows(rows, center_id=center_id)
    finally:
        eng.dispose()
