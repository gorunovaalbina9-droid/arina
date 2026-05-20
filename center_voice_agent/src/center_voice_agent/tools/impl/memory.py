from __future__ import annotations

from typing import Optional

from center_voice_agent.memory.repository import LongTermMemoryRepository


async def memory_search_text(
    repo: LongTermMemoryRepository,
    child_profile_id: str,
    query: str,
    *,
    limit: int = 5,
) -> str:
    return await repo.search(child_profile_id, query, limit=limit)


async def memory_upsert_text(
    repo: LongTermMemoryRepository,
    child_profile_id: str,
    category: str,
    value_text: str,
    *,
    key: Optional[str] = None,
) -> str:
    return await repo.upsert(child_profile_id, category, value_text, key=key)
