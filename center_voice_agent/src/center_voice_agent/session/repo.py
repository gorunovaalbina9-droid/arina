from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass
class SessionRow:
    session_id: str
    child_profile_id: str
    mode_id: str
    scenario_id: Optional[str]
    scenario_node_id: Optional[str]
    state_json: str


class SessionStateRepository:
    """Сессия: текущий режим и привязка к ребёнку (таблица session_state)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get(self, session_id: str) -> Optional[SessionRow]:
        async with self._session_factory() as session:
            r = await session.execute(
                text(
                    """
                    SELECT session_id, child_profile_id, mode_id, scenario_id, scenario_node_id, state_json
                    FROM session_state WHERE session_id = :sid
                    """
                ),
                {"sid": session_id},
            )
            row = r.mappings().first()
            if not row:
                return None
            return SessionRow(
                session_id=str(row["session_id"]),
                child_profile_id=str(row["child_profile_id"]),
                mode_id=str(row["mode_id"]),
                scenario_id=row.get("scenario_id"),
                scenario_node_id=row.get("scenario_node_id"),
                state_json=str(row["state_json"] or "{}"),
            )

    async def ensure(
        self,
        session_id: str,
        child_profile_id: str,
        *,
        default_mode_id: str,
    ) -> SessionRow:
        existing = await self.get(session_id)
        if existing:
            return existing
        state = json.dumps({"version": 1}, ensure_ascii=False)
        async with self._session_factory() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO session_state (session_id, child_profile_id, mode_id, scenario_id, scenario_node_id, state_json, updated_at)
                    VALUES (:sid, :child, :mode, NULL, NULL, :sj, datetime('now'))
                    """
                ),
                {"sid": session_id, "child": child_profile_id, "mode": default_mode_id, "sj": state},
            )
            await session.commit()
        row = await self.get(session_id)
        assert row is not None
        return row

    async def set_mode(self, session_id: str, mode_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                text(
                    """
                    UPDATE session_state SET mode_id = :mode, updated_at = datetime('now')
                    WHERE session_id = :sid
                    """
                ),
                {"sid": session_id, "mode": mode_id},
            )
            await session.commit()

    async def update_scenario_pointer(
        self,
        session_id: str,
        *,
        scenario_id: Optional[str],
        scenario_node_id: Optional[str],
    ) -> None:
        async with self._session_factory() as session:
            await session.execute(
                text(
                    """
                    UPDATE session_state
                    SET scenario_id = :sc, scenario_node_id = :node, updated_at = datetime('now')
                    WHERE session_id = :sid
                    """
                ),
                {"sid": session_id, "sc": scenario_id, "node": scenario_node_id},
            )
            await session.commit()

    async def attach_scenario(self, session_id: str, scenario_id: str, *, node_id: Optional[str] = None) -> None:
        """Привязать активный сценарий к сессии (node_id NULL = entry при следующей загрузке)."""
        await self.update_scenario_pointer(session_id, scenario_id=scenario_id, scenario_node_id=node_id)
