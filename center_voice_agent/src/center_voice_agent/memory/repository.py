from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from center_voice_agent.db.dialect import (
    DbDialect,
    coalesce_empty_sql,
    insert_child_profile_ignore_sql,
    now_sql,
)
from center_voice_agent.memory.categories import ALLOWED_MEMORY_CATEGORIES

log = structlog.get_logger(__name__)


@dataclass
class MemoryEntryRow:
    id: str
    category: str
    key: Optional[str]
    value_text: str
    updated_at: str


class LongTermMemoryRepository:
    """Долгосрочная память: SQLite/PG через async SQLAlchemy."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        dialect: DbDialect = "sqlite",
    ) -> None:
        self._session_factory = session_factory
        self._dialect = dialect
        self._now = now_sql(dialect)

    async def ensure_child_profile(
        self,
        child_profile_id: str,
        *,
        center_id: str = "default-center",
    ) -> None:
        async with self._session_factory() as session:
            await session.execute(
                text(insert_child_profile_ignore_sql(self._dialect)),
                {"id": child_profile_id, "center_id": center_id},
            )
            await session.commit()

    async def search(
        self,
        child_profile_id: str,
        query: str,
        *,
        limit: int = 5,
    ) -> str:
        """Текстовый поиск по value_text / key / category для подстановки в промпт."""
        strip_q = query.strip()
        wide = 1 if not strip_q else 0
        if strip_q:
            escaped = (
                strip_q.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            like = f"%{escaped}%"
        else:
            like = "%"
        key_expr = coalesce_empty_sql(self._dialect, "key")
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, category, key, value_text, updated_at
                    FROM long_term_memory_entries
                    WHERE child_profile_id = :child
                      AND (
                        :wide = 1
                        OR value_text LIKE :like ESCAPE '\\'
                        OR {key_expr} LIKE :like ESCAPE '\\'
                        OR category LIKE :like ESCAPE '\\'
                      )
                    ORDER BY updated_at DESC
                    LIMIT :limit
                    """
                ),
                {
                    "child": child_profile_id,
                    "wide": wide,
                    "like": like,
                    "limit": limit,
                },
            )
            rows = result.mappings().all()

        if not rows:
            return "(записей в долгосрочной памяти не найдено)"

        lines: list[str] = []
        for r in rows:
            k = r["key"] or ""
            prefix = f"[{r['category']}]"
            if k:
                prefix += f" {k}:"
            else:
                prefix += ""
            lines.append(f"- {prefix} {r['value_text']}")
        return "\n".join(lines)

    async def upsert(
        self,
        child_profile_id: str,
        category: str,
        value_text: str,
        *,
        key: Optional[str] = None,
        source: str = "agent",
    ) -> str:
        if category not in ALLOWED_MEMORY_CATEGORIES:
            allowed = ", ".join(sorted(ALLOWED_MEMORY_CATEGORIES))
            return f"Ошибка: категория «{category}» не разрешена. Разрешены: {allowed}."

        await self.ensure_child_profile(child_profile_id)
        vid = str(uuid.uuid4())
        now_expr = self._now

        async with self._session_factory() as session:
            if key is not None:
                cur = await session.execute(
                    text(
                        """
                        SELECT id FROM long_term_memory_entries
                        WHERE child_profile_id = :child AND category = :cat AND key = :key
                        LIMIT 1
                        """
                    ),
                    {"child": child_profile_id, "cat": category, "key": key},
                )
                existing = cur.scalar_one_or_none()
                if existing:
                    await session.execute(
                        text(
                            f"""
                            UPDATE long_term_memory_entries
                            SET value_text = :val, source = :src, updated_at = {now_expr}
                            WHERE id = :id
                            """
                        ),
                        {"val": value_text, "src": source, "id": existing},
                    )
                    await session.commit()
                    log.info("memory_upsert_update", memory_id=existing, category=category)
                    return "Запись обновлена."

            await session.execute(
                text(
                    f"""
                    INSERT INTO long_term_memory_entries
                        (id, child_profile_id, category, key, value_text, source, updated_at, created_at)
                    VALUES
                        (:id, :child, :cat, :key, :val, :src, {now_expr}, {now_expr})
                    """
                ),
                {
                    "id": vid,
                    "child": child_profile_id,
                    "cat": category,
                    "key": key,
                    "val": value_text,
                    "src": source,
                },
            )
            await session.commit()
            log.info("memory_upsert_insert", memory_id=vid, category=category)
            return "Запись добавлена."

    async def list_entries(
        self,
        child_profile_id: str,
        category: str,
        *,
        limit: int = 50,
    ) -> list[MemoryEntryRow]:
        """Список записей долгой памяти по категории (для отчётов вне агента)."""
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT id, category, key, value_text, updated_at
                    FROM long_term_memory_entries
                    WHERE child_profile_id = :child AND category = :cat
                    ORDER BY updated_at DESC
                    LIMIT :limit
                    """
                ),
                {"child": child_profile_id, "cat": category, "limit": limit},
            )
            rows = result.mappings().all()
        return [
            MemoryEntryRow(
                id=str(r["id"]),
                category=str(r["category"]),
                key=r["key"],
                value_text=str(r["value_text"]),
                updated_at=str(r["updated_at"]),
            )
            for r in rows
        ]
