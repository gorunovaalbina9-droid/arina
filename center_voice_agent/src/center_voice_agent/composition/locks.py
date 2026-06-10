"""Общие asyncio-локи процесса (без импорта AppContainer)."""

from __future__ import annotations

import asyncio

_publish_lock = asyncio.Lock()


def get_publish_lock() -> asyncio.Lock:
    return _publish_lock
