from __future__ import annotations

import argparse
import asyncio

from center_voice_agent.composition.runtime import get_process_container, shutdown_process_container
from center_voice_agent.security.retention import (
    purge_old_session_messages,
    purge_stale_session_state,
)
from center_voice_agent.settings import get_settings


async def _run(*, messages_days: int | None, state_days: int | None) -> None:
    settings = get_settings()
    container = await get_process_container(settings)
    try:
        md = messages_days if messages_days is not None else settings.session_messages_retention_days
        sd = state_days if state_days is not None else settings.session_state_retention_days
        n_msg = await purge_old_session_messages(container.engine, retention_days=md)
        n_state = await purge_stale_session_state(container.engine, retention_days=sd)
        print(f"session_messages deleted: {n_msg} (>{md} days)")
        print(f"session_state deleted: {n_state} (>{sd} days)")
    finally:
        await shutdown_process_container()


def main() -> None:
    parser = argparse.ArgumentParser(description="Retention: purge старых session_messages / session_state")
    parser.add_argument("--messages-days", type=int, default=None, help="Override SESSION_MESSAGES_RETENTION_DAYS")
    parser.add_argument("--state-days", type=int, default=None, help="Override SESSION_STATE_RETENTION_DAYS")
    args = parser.parse_args()
    asyncio.run(_run(messages_days=args.messages_days, state_days=args.state_days))


if __name__ == "__main__":
    main()
