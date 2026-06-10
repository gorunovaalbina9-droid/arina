"""Async-публикация режимов и сценариев (общий engine с runtime)."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from center_voice_agent.composition.locks import get_publish_lock
from center_voice_agent.db.dialect import detect_dialect, now_sql


def _ts(engine: AsyncEngine) -> str:
    return now_sql(detect_dialect(str(engine.url)))


async def publish_mode_yaml(
    engine: AsyncEngine,
    *,
    config_yaml: str,
    mode_id: str,
    center_id: Optional[str] = None,
    status: str = "published",
) -> str:
    rid = str(uuid.uuid4())
    ts = _ts(engine)
    async with get_publish_lock():
        async with engine.begin() as conn:
            if status == "published":
                await conn.execute(
                    text(
                        """
                        DELETE FROM mode_definitions
                        WHERE mode_id = :mid AND status = 'published'
                          AND (center_id IS :cid OR (center_id IS NULL AND :cid IS NULL))
                        """
                    ),
                    {"mid": mode_id, "cid": center_id},
                )
            cur = await conn.execute(
                text(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM mode_definitions WHERE mode_id = :mid"
                ),
                {"mid": mode_id},
            )
            nxt = int(cur.scalar() or 1)
            await conn.execute(
                text(
                    f"""
                    INSERT INTO mode_definitions (
                        id, mode_id, center_id, status, version, config_yaml, updated_at, created_at
                    )
                    VALUES (
                        :id, :mid, :cid, :st, :ver, :yaml,
                        {ts}, {ts}
                    )
                    """
                ),
                {
                    "id": rid,
                    "mid": mode_id,
                    "cid": center_id,
                    "st": status,
                    "ver": nxt,
                    "yaml": config_yaml,
                },
            )
    return rid


async def publish_scenario_yaml(
    engine: AsyncEngine,
    *,
    config_yaml: str,
    scenario_id: str,
    center_id: Optional[str] = None,
    status: str = "published",
    subject: Optional[str] = None,
    age_band: Optional[str] = None,
) -> str:
    rid = str(uuid.uuid4())
    ts = _ts(engine)
    async with get_publish_lock():
        async with engine.begin() as conn:
            if status == "published":
                await conn.execute(
                    text(
                        """
                        DELETE FROM scenario_publish
                        WHERE scenario_id = :sid AND status = 'published'
                          AND (center_id IS :cid OR (center_id IS NULL AND :cid IS NULL))
                        """
                    ),
                    {"sid": scenario_id, "cid": center_id},
                )
            cur = await conn.execute(
                text(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM scenario_publish WHERE scenario_id = :sid"
                ),
                {"sid": scenario_id},
            )
            nxt = int(cur.scalar() or 1)
            await conn.execute(
                text(
                    f"""
                    INSERT INTO scenario_publish (
                        id, scenario_id, center_id, status, version, config_yaml,
                        subject, age_band, updated_at, created_at
                    )
                    VALUES (
                        :id, :sid, :cid, :st, :ver, :yaml, :subj, :band,
                        {ts}, {ts}
                    )
                    """
                ),
                {
                    "id": rid,
                    "sid": scenario_id,
                    "cid": center_id,
                    "st": status,
                    "ver": nxt,
                    "yaml": config_yaml,
                    "subj": subject,
                    "band": age_band,
                },
            )
    return rid
