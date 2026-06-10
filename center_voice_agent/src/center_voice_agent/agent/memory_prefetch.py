"""Prefetch долгосрочной памяти перед ходом LLM."""

from __future__ import annotations

from typing import Optional

from center_voice_agent.memory.repository import LongTermMemoryRepository
from center_voice_agent.settings import Settings


async def resolve_long_term_summary(
    repo: LongTermMemoryRepository,
    settings: Settings,
    child_profile_id: str,
    *,
    long_term_summary: Optional[str] = None,
) -> Optional[str]:
    if long_term_summary is not None:
        return long_term_summary
    if not settings.prefetch_long_term_memory:
        return None
    await repo.ensure_child_profile(child_profile_id)
    return await repo.search(
        child_profile_id,
        "",
        limit=settings.prefetch_memory_limit,
    )
