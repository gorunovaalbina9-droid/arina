from __future__ import annotations

import uuid
from typing import Literal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from center_voice_agent.context.short_term import Role

MessageRole = Literal["user", "assistant"]


class SessionMessagesRepository:
    """Персистентная краткосрочная память: последние реплики по session_id."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def append(self, session_id: str, role: MessageRole, content_text: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO session_messages (id, session_id, role, content_text, created_at)
                    VALUES (:id, :sid, :role, :text, datetime('now'))
                    """
                ),
                {"id": str(uuid.uuid4()), "sid": session_id, "role": role, "text": content_text},
            )
            await session.commit()

    async def load_recent(self, session_id: str, *, limit: int) -> list[tuple[Role, str]]:
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT role, content_text FROM (
                        SELECT role, content_text, rowid AS rid
                        FROM session_messages
                        WHERE session_id = :sid
                        ORDER BY rowid DESC
                        LIMIT :lim
                    ) sub
                    ORDER BY sub.rid ASC
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
                    """
                    SELECT id FROM session_messages
                    WHERE session_id = :sid
                    ORDER BY rowid ASC
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
