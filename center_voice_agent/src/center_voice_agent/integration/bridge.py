"""
Простой мост для внешних программ: текст пользователя → ответ наставника.

Для голосового GUI: один раз AgentSession.open(), много ask(), в конце close().
ask_once / ask_once_sync — только отладка (создают сессию на каждый вызов).

Пример (async):
    session = await AgentSession.open(child_profile_id="child-1", age_band="5-6")
    answer = await session.ask("Привет!")
    await session.close()

Пример (sync, для GUI):
    from center_voice_agent.integration.bridge import ask_once_sync
    text = ask_once_sync("Привет!", session_id="room-1", child_profile_id="child-1")
"""

from __future__ import annotations

import asyncio
from typing import Optional

from center_voice_agent.agent.gateway import AgentTurnResult
from center_voice_agent.composition.container import AppContainer
from center_voice_agent.composition.runtime import (
    get_process_container,
    shutdown_process_container,
)
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.context.short_term_factory import build_short_term_memory
from center_voice_agent.orchestration.coordinator import SessionCoordinator
from center_voice_agent.settings import Settings, get_settings


class AgentSession:
    """Одна сессия диалога: память 15 реплик + режим/сценарий в SQLite."""

    def __init__(
        self,
        *,
        coordinator: SessionCoordinator,
        container: AppContainer,
        short_term: ShortTermMemory,
        session_id: str,
        child_profile_id: str,
        age_band: Optional[str] = None,
        owns_container: bool = False,
    ) -> None:
        self._gateway = coordinator.gateway
        self._coord = coordinator
        self._container = container
        self._stm = short_term
        self._owns_container = owns_container
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
        offline_llm: bool = False,
    ) -> AgentSession:
        settings = settings or get_settings()
        container = await get_process_container(settings)
        llm = None
        if offline_llm:
            from center_voice_agent.agent.fake_llm import StaticChatModel

            llm = StaticChatModel(reply="Привет! Я Арина. Рада тебя слышать.")
        coord = container.build_coordinator(llm=llm)
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
            container=container,
            short_term=stm,
            session_id=session_id,
            child_profile_id=child_profile_id,
            age_band=age_band,
            owns_container=False,
        )

    @classmethod
    async def open_with_container(
        cls,
        container: AppContainer,
        *,
        session_id: str,
        child_profile_id: str,
        age_band: Optional[str] = None,
        scenario_id: Optional[str] = None,
        llm=None,
        owns_container: bool = False,
    ) -> AgentSession:
        """Для тестов и кастомной сборки."""
        settings = container.settings
        coord = container.build_coordinator(llm=llm)
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
            container=container,
            short_term=stm,
            session_id=session_id,
            child_profile_id=child_profile_id,
            age_band=age_band,
            owns_container=owns_container,
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
        if self._owns_container:
            await self._container.aclose()


async def ask_once(
    user_text: str,
    *,
    session_id: str,
    child_profile_id: str = "child-default",
    age_band: Optional[str] = "5-6",
    scenario_id: Optional[str] = None,
    offline_llm: bool = False,
) -> str:
    """Один вопрос — один ответ (сессия создаётся; engine процесса не закрывается)."""
    session = await AgentSession.open(
        session_id=session_id,
        child_profile_id=child_profile_id,
        age_band=age_band,
        scenario_id=scenario_id,
        offline_llm=offline_llm,
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
    offline_llm: bool = False,
) -> str:
    """Синхронная обёртка для GUI (voice_assistant и т.п.)."""
    return asyncio.run(
        ask_once(
            user_text,
            session_id=session_id,
            child_profile_id=child_profile_id,
            age_band=age_band,
            scenario_id=scenario_id,
            offline_llm=offline_llm,
        )
    )


__all__ = [
    "AgentSession",
    "ask_once",
    "ask_once_sync",
    "shutdown_process_container",
]
