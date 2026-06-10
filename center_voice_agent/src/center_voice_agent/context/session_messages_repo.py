from __future__ import annotations

import uuid
from typing import Literal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from center_voice_agent.context.short_term import Role
from center_voice_agent.db.dialect import DbDialect, now_sql

MessageRole = Literal["user", "assistant"]


class SessionMessagesRepository:
    """Персистентная краткосрочная память: последние реплики по session_id."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        dialect: DbDialect = "sqlite",
    ) -> None:
        self._session_factory = session_factory
        self._dialect = dialect
        self._now = now_sql(dialect)
        if dialect == "postgresql":
            self._order_desc = "created_at DESC, id DESC"
            self._order_asc = "created_at ASC, id ASC"
            self._recent_inner = "role, content_text, created_at, id"
            self._recent_outer = "sub.created_at ASC, sub.id ASC"
        else:
            self._order_desc = "rowid DESC"
            self._order_asc = "rowid ASC"
            self._recent_inner = "role, content_text, rowid AS rid"
            self._recent_outer = "sub.rid ASC"

    async def append(self, session_id: str, role: MessageRole, content_text: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO session_messages (id, session_id, role, content_text, created_at)
                    VALUES (:id, :sid, :role, :text, {self._now})
                    """
                ),
                {"id": str(uuid.uuid4()), "sid": session_id, "role": role, "text": content_text},
            )
            await session.commit()

    async def load_recent(self, session_id: str, *, limit: int) -> list[tuple[Role, str]]:
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT role, content_text FROM (
                        SELECT {self._recent_inner}
                        FROM session_messages
                        WHERE session_id = :sid
                        ORDER BY {self._order_desc}
                        LIMIT :lim
                    ) sub
                    ORDER BY {self._recent_outer}
                    """
                ),
                {"sid": session_id, "lim": limit},
            )
            rows = result.mappings().all()
        out: list[tuple[Role, str]] = []
        for row in rows:
            role = str(row["role"])
            if role not in ("user", "assistant"):
                continue
            out.append((role, str(row["content_text"])))
        return out

    async def trim(self, session_id: str, *, keep: int) -> None:
        if keep < 1:
            return
        async with self._session_factory() as session:
            count_r = await session.execute(
                text("SELECT COUNT(*) AS c FROM session_messages WHERE session_id = :sid"),
                {"sid": session_id},
            )
            total = int(count_r.scalar_one() or 0)
            excess = total - keep
            if excess <= 0:
                return
            old = await session.execute(
                text(
                    f"""
                    SELECT id FROM session_messages
                    WHERE session_id = :sid
                    ORDER BY {self._order_asc}
                    LIMIT :excess
                    """
                ),
                {"sid": session_id, "excess": excess},
            )
            ids = [str(r[0]) for r in old.fetchall()]
            for mid in ids:
                await session.execute(
                    text("DELETE FROM session_messages WHERE id = :id"),
                    {"id": mid},
                )
            await session.commit()
