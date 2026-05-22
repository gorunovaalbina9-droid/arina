"""
Простой мост для внешних программ: текст пользователя → ответ наставника.

Пример (async):
    session = await AgentSession.open(child_profile_id="child-1", age_band="5-6")
    answer = await session.ask("Привет!")
    await session.close()

Пример (sync, для GUI):
    from center_voice_agent.integration.bridge import ask_once
    text = ask_once("Привет!", session_id="room-1", child_profile_id="child-1")
"""

from __future__ import annotations

import asyncio
from typing import Optional

from center_voice_agent.agent.gateway import AgentTurnResult
from center_voice_agent.composition.container import AppContainer
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.context.short_term_factory import build_short_term_memory
from center_voice_agent.db.session import init_database
from center_voice_agent.orchestration.coordinator import SessionCoordinator
from center_voice_agent.settings import Settings, get_settings

_init_lock = asyncio.Lock()
_db_ready = False


async def _ensure_db(settings: Settings) -> None:
    global _db_ready
    if _db_ready:
        return
    async with _init_lock:
        if _db_ready:
            return
        await init_database(settings.project_root, settings.database_url)
        _db_ready = True


class AgentSession:
    """Одна сессия диалога: память 15 реплик + режим/сценарий в SQLite."""

    def __init__(
        self,
        *,
        coordinator: SessionCoordinator,
        short_term: ShortTermMemory,
        session_id: str,
        child_profile_id: str,
        age_band: Optional[str] = None,
    ) -> None:
        self._gateway = coordinator.gateway
        self._coord = coordinator
        self._stm = short_term
        self.session_id = session_id
        self.child_profile_id = child_profile_id
        self.age_band = age_band

    @classmethod
    async def open(
        cls,
        *,
        session_id: str,
        child_profile_id: str,
        age_band: Optional[str] = None,
        scenario_id: Optional[str] = None,
        settings: Optional[Settings] = None,
    ) -> AgentSession:
        settings = settings or get_settings()
        await _ensure_db(settings)
        container = AppContainer.from_settings(settings)
        coord = container.build_coordinator()
        await coord.gateway.session_repository.ensure(
            session_id, child_profile_id, default_mode_id=settings.default_mode_id
        )
        stm = await build_short_term_memory(
            session_id,
            settings=settings,
            messages_repo=container.session_messages_repository,
        )
        if scenario_id:
            await coord.gateway.session_repository.attach_scenario(session_id, scenario_id)
        return cls(
            coordinator=coord,
            short_term=stm,
            session_id=session_id,
            child_profile_id=child_profile_id,
            age_band=age_band,
        )

    async def ask(self, user_text: str) -> AgentTurnResult:
        return await self._coord.handle_user_turn(
            session_id=self.session_id,
            child_profile_id=self.child_profile_id,
            user_text=user_text,
            short_term=self._stm,
            age_band=self.age_band,
        )

    def spoken_text(self, result: AgentTurnResult) -> str:
        return (result.reply_spoken or result.text or "").strip()

    async def reload_modes(self) -> list[str]:
        """Перечитать YAML/БД в этом процессе (после modes_publish)."""
        return self._coord.gateway.modes.reload_all()

    async def close(self) -> None:
        await self._coord.gateway.aclose()


async def ask_once(
    user_text: str,
    *,
    session_id: str,
    child_profile_id: str = "child-default",
    age_band: Optional[str] = "5-6",
    scenario_id: Optional[str] = None,
) -> str:
    """Один вопрос — один ответ (сессия создаётся и закрывается)."""
    session = await AgentSession.open(
        session_id=session_id,
        child_profile_id=child_profile_id,
        age_band=age_band,
        scenario_id=scenario_id,
    )
    try:
        result = await session.ask(user_text)
        return session.spoken_text(result)
    finally:
        await session.close()


def ask_once_sync(
    user_text: str,
    *,
    session_id: str,
    child_profile_id: str = "child-default",
    age_band: Optional[str] = "5-6",
    scenario_id: Optional[str] = None,
) -> str:
    """Синхронная обёртка для GUI (voice_assistant и т.п.)."""
    return asyncio.run(
        ask_once(
            user_text,
            session_id=session_id,
            child_profile_id=child_profile_id,
            age_band=age_band,
            scenario_id=scenario_id,
        )
    )
