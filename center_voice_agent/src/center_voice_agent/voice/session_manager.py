"""
Долгоживущие сессии для голосового GUI: один AppContainer + кэш AgentSession по session_id.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from center_voice_agent.integration.bridge import AgentSession


@dataclass
class VoiceSessionManager:
    """Кэш сессий в RAM процесса (не закрывать engine между репликами)."""

    _sessions: dict[str, AgentSession] = field(default_factory=dict)

    async def ask(
        self,
        user_text: str,
        *,
        session_id: str,
        child_profile_id: str = "child-default",
        age_band: Optional[str] = "5-6",
        scenario_id: Optional[str] = None,
        offline_llm: bool = False,
    ) -> str:
        session = await self._get_or_open(
            session_id=session_id,
            child_profile_id=child_profile_id,
            age_band=age_band,
            scenario_id=scenario_id,
            offline_llm=offline_llm,
        )
        result = await session.ask(user_text)
        return session.spoken_text(result)

    async def _get_or_open(
        self,
        *,
        session_id: str,
        child_profile_id: str,
        age_band: Optional[str],
        scenario_id: Optional[str],
        offline_llm: bool,
    ) -> AgentSession:
        existing = self._sessions.get(session_id)
        if existing is not None:
            return existing
        session = await AgentSession.open(
            session_id=session_id,
            child_profile_id=child_profile_id,
            age_band=age_band,
            scenario_id=scenario_id,
            offline_llm=offline_llm,
        )
        self._sessions[session_id] = session
        return session

    async def close_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session is not None:
            await session.close()

    async def close_all(self) -> None:
        for sid in list(self._sessions.keys()):
            await self.close_session(sid)

    def reset(self) -> None:
        self._sessions.clear()


_manager = VoiceSessionManager()


def get_voice_session_manager() -> VoiceSessionManager:
    return _manager


def reset_voice_sessions_for_tests() -> None:
    _manager.reset()


def ask_voice_sync(
    user_text: str,
    *,
    session_id: str,
    child_profile_id: str = "child-default",
    age_band: Optional[str] = "5-6",
    scenario_id: Optional[str] = None,
    offline_llm: bool = False,
) -> str:
    """Синхронный hot path для voice_assistant: переиспользует сессию и container."""
    return asyncio.run(
        _manager.ask(
            user_text,
            session_id=session_id,
            child_profile_id=child_profile_id,
            age_band=age_band,
            scenario_id=scenario_id,
            offline_llm=offline_llm,
        )
    )
