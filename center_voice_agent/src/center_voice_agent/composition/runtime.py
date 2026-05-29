"""
Жизненный цикл процесса: один AppContainer, блокировка publish.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from center_voice_agent.composition.container import AppContainer
from center_voice_agent.db.session import init_database
from center_voice_agent.settings import Settings, get_settings

_process_container: Optional[AppContainer] = None
_process_lock = asyncio.Lock()
_publish_lock = asyncio.Lock()


def get_publish_lock() -> asyncio.Lock:
    """Сериализация publish режимов/сценариев и ходов диалога (SQLite)."""
    return _publish_lock


async def get_process_container(settings: Optional[Settings] = None) -> AppContainer:
    """Один контейнер и engine на процесс (voice GUI, API)."""
    global _process_container
    if _process_container is not None:
        return _process_container
    async with _process_lock:
        if _process_container is not None:
            return _process_container
        s = settings or get_settings()
        await init_database(s.project_root, s.database_url)
        _process_container = AppContainer.from_settings(s)
        return _process_container


async def shutdown_process_container() -> None:
    global _process_container
    async with _process_lock:
        if _process_container is not None:
            await _process_container.aclose()
            _process_container = None


def reset_process_runtime_for_tests() -> None:
    """Сброс singleton между тестами (без dispose — вызывайте shutdown при необходимости)."""
    global _process_container
    _process_container = None
