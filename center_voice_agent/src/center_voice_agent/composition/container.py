"""
Сборка зависимостей из Settings (единственная точка чтения env — settings.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from langchain_core.language_models import BaseChatModel
from sqlalchemy.ext.asyncio import AsyncEngine

from center_voice_agent.agent.prompt_builder import TurnPromptBuilder
from center_voice_agent.age_bands.loader import load_age_bands
from center_voice_agent.db.dialect import detect_dialect
from center_voice_agent.db.session import create_engine_and_session_factory, ensure_sqlite_parent_dir
from center_voice_agent.context.session_messages_repo import SessionMessagesRepository
from center_voice_agent.memory.repository import LongTermMemoryRepository
from center_voice_agent.modes.registry import ModeRegistry
from center_voice_agent.orchestration.coordinator import SessionCoordinator
from center_voice_agent.security.rate_limit import InMemoryRateLimiter, RateLimiter
from center_voice_agent.security.rate_limit_factory import build_rate_limiter
from center_voice_agent.session.repo import SessionStateRepository
from center_voice_agent.settings import Settings, get_settings


@dataclass
class AppContainer:
    """Инфраструктура: Settings, БД, репозитории, реестр режимов, сборщик промпта."""

    settings: Settings
    mode_registry: ModeRegistry
    memory_repository: LongTermMemoryRepository
    session_repository: SessionStateRepository
    session_messages_repository: SessionMessagesRepository
    prompt_builder: TurnPromptBuilder
    age_bands: dict
    rate_limiter: RateLimiter = field(default_factory=InMemoryRateLimiter)
    _engine: Optional[AsyncEngine] = None

    @classmethod
    def from_settings(
        cls,
        settings: Optional[Settings] = None,
        *,
        memory_repository: Optional[LongTermMemoryRepository] = None,
    ) -> AppContainer:
        s = settings or get_settings()
        ensure_sqlite_parent_dir(s.database_url)
        engine, session_factory = create_engine_and_session_factory(s.database_url)
        dialect = detect_dialect(s.database_url)
        memory = memory_repository or LongTermMemoryRepository(session_factory, dialect=dialect)
        modes = ModeRegistry(
            s.modes_dir,
            project_root=s.project_root,
            database_url=s.database_url,
            modes_source=s.modes_source,
            modes_center_id=s.modes_center_id,
        )
        bands = load_age_bands(s.age_bands_path)
        limiter = build_rate_limiter(s)
        return cls(
            settings=s,
            mode_registry=modes,
            memory_repository=memory,
            session_repository=SessionStateRepository(session_factory, dialect=dialect),
            session_messages_repository=SessionMessagesRepository(session_factory, dialect=dialect),
            prompt_builder=TurnPromptBuilder(age_bands=bands),
            age_bands=bands,
            rate_limiter=limiter,
            _engine=engine,
        )

    def build_gateway(self, *, llm: Optional[BaseChatModel] = None):
        from center_voice_agent.agent.gateway import AgentGateway

        return AgentGateway(container=self, llm=llm)

    def build_coordinator(self, *, llm: Optional[BaseChatModel] = None) -> SessionCoordinator:
        gateway = self.build_gateway(llm=llm)
        return SessionCoordinator(
            gateway,
            settings=self.settings,
            mode_registry=self.mode_registry,
            session_repository=self.session_repository,
            session_messages_repository=self.session_messages_repository,
            rate_limiter=self.rate_limiter,
            engine=self._engine,
        )

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("AppContainer engine не инициализирован")
        return self._engine

    async def aclose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
