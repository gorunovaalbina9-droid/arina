"""Проверка согласия родителя (152-ФЗ) — meta_json в child_profiles."""

from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

import structlog

log = structlog.get_logger(__name__)


async def parent_consent_recorded(
    session_factory: async_sessionmaker[AsyncSession],
    child_profile_id: str,
) -> bool:
    async with session_factory() as session:
        r = await session.execute(
            text("SELECT meta_json FROM child_profiles WHERE id = :id"),
            {"id": child_profile_id},
        )
        row = r.mappings().first()
    if not row:
        return False
    raw = row.get("meta_json")
    if not raw:
        return False
    try:
        meta = json.loads(str(raw))
    except json.JSONDecodeError:
        return False
    if not isinstance(meta, dict):
        return False
    return bool(meta.get("parent_consent_at") or meta.get("parent_consent"))


async def check_parent_consent_required(
    session_factory: async_sessionmaker[AsyncSession],
    child_profile_id: str,
    *,
    require: bool,
) -> Optional[str]:
    """None если можно продолжать, иначе reason для security_incident."""
    if not require:
        return None
    if await parent_consent_recorded(session_factory, child_profile_id):
        return None
    log.info("consent_missing", child_profile_id=child_profile_id)
    return "consent_required:parent"
