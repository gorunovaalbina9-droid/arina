from __future__ import annotations

from typing import Optional

from center_voice_agent.context.session_messages_repo import SessionMessagesRepository
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.settings import Settings


async def build_short_term_memory(
    session_id: str,
    *,
    settings: Settings,
    messages_repo: Optional[SessionMessagesRepository] = None,
) -> ShortTermMemory:
    """RAM по умолчанию; при SHORT_TERM_SOURCE=db — загрузка последних реплик из SQLite."""
    max_turns = settings.short_term_max_messages
    if settings.short_term_source != "db":
        return ShortTermMemory(max_turns=max_turns)
    if messages_repo is None:
        return ShortTermMemory(max_turns=max_turns)
    pairs = await messages_repo.load_recent(session_id, limit=max_turns)
    return ShortTermMemory.from_pairs(pairs, max_turns=max_turns)


async def persist_turn_messages(
    session_id: str,
    user_text: str,
    assistant_text: str,
    *,
    settings: Settings,
    messages_repo: Optional[SessionMessagesRepository],
) -> None:
    if settings.short_term_source != "db" or messages_repo is None:
        return
    reply = (assistant_text or "").strip()
    if not reply:
        return
    await messages_repo.append(session_id, "user", user_text)
    await messages_repo.append(session_id, "assistant", reply)
    await messages_repo.trim(session_id, keep=settings.short_term_max_messages)
