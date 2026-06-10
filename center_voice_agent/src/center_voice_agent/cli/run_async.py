from __future__ import annotations

import asyncio
from typing import Callable, Coroutine, TypeVar

T = TypeVar("T")


def run_async_main(factory: Callable[[], Coroutine[None, None, T]]) -> T:
    return asyncio.run(factory())


def init_db_entry() -> None:
    from center_voice_agent.cli import init_db

    run_async_main(init_db.main)


def create_child_entry() -> None:
    from center_voice_agent.cli import create_child

    run_async_main(create_child.main)


def demo_turn_entry() -> None:
    from center_voice_agent.cli import demo_turn

    run_async_main(demo_turn.main)


def text_turn_entry() -> None:
    from center_voice_agent.cli import text_turn

    run_async_main(text_turn.main)


def live_turn_entry() -> None:
    from center_voice_agent.cli import live_turn

    run_async_main(live_turn.main)


def memory_roundtrip_entry() -> None:
    from center_voice_agent.cli import memory_roundtrip

    run_async_main(memory_roundtrip.main)


def block2_offline_entry() -> None:
    from center_voice_agent.cli import block2_offline

    run_async_main(block2_offline.main)
