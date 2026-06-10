"""Запуск coroutine из sync- и async-контекста."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

T = TypeVar("T")


def run_coroutine_sync(factory: Callable[[], Coroutine[None, None, T]]) -> T:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(factory())
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(lambda: asyncio.run(factory())).result()
