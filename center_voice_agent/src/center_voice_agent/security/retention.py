"""Retention: очистка session_messages и ротация логов."""

from __future__ import annotations

from pathlib import Path

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from center_voice_agent.db.dialect import days_ago_sql, detect_dialect

log = structlog.get_logger(__name__)


async def purge_old_session_messages(engine: AsyncEngine, *, retention_days: int) -> int:
    """Удаляет session_messages старше retention_days. Возвращает число удалённых строк."""
    if retention_days < 1:
        return 0
    dialect = detect_dialect(str(engine.url))
    cutoff = days_ago_sql(dialect, retention_days)
    async with engine.begin() as conn:
        result = await conn.execute(
            text(f"DELETE FROM session_messages WHERE created_at < {cutoff}")
        )
        deleted = int(result.rowcount or 0)
    if deleted:
        log.info("retention_purge_session_messages", deleted=deleted, retention_days=retention_days)
    return deleted


async def purge_stale_session_state(engine: AsyncEngine, *, retention_days: int) -> int:
    """Удаляет session_state без активности дольше retention_days."""
    if retention_days < 1:
        return 0
    dialect = detect_dialect(str(engine.url))
    cutoff = days_ago_sql(dialect, retention_days)
    async with engine.begin() as conn:
        result = await conn.execute(
            text(f"DELETE FROM session_state WHERE updated_at < {cutoff}")
        )
        deleted = int(result.rowcount or 0)
    if deleted:
        log.info("retention_purge_session_state", deleted=deleted, retention_days=retention_days)
    return deleted


def rotate_log_file(path: Path, *, max_bytes: int, backup_count: int) -> None:
    """Ротация agent.log: file → .1 → .2 … (backup_count копий)."""
    if backup_count < 1 or not path.is_file() or path.stat().st_size <= max_bytes:
        return
    oldest = path.with_name(f"{path.name}.{backup_count}")
    if oldest.is_file():
        oldest.unlink()
    for i in range(backup_count - 1, 0, -1):
        src = path.with_name(f"{path.name}.{i}")
        dst = path.with_name(f"{path.name}.{i + 1}")
        if src.is_file():
            src.replace(dst)
    path.replace(path.with_name(f"{path.name}.1"))
    path.touch()
