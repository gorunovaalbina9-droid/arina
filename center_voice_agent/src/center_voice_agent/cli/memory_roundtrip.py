"""
Проверка памяти без LLM: memory_upsert → SQLite → memory_search (шаг 2.3).

  python -m center_voice_agent.cli.memory_roundtrip
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from center_voice_agent.db.session import init_database
from center_voice_agent.memory.repository import LongTermMemoryRepository
from center_voice_agent.settings import get_settings
from center_voice_agent.tools.factory import build_tools_for_mode
from center_voice_agent.tools.impl import memory as memory_impl


async def main() -> None:
    settings = get_settings()
    await init_database(settings.project_root, settings.database_url)

    from center_voice_agent.db.session import create_engine_and_session_factory

    _, session_factory = create_engine_and_session_factory(settings.database_url)
    repo = LongTermMemoryRepository(session_factory)
    child_id = f"child-mem-{uuid.uuid4().hex[:6]}"
    marker = f"roundtrip-{uuid.uuid4().hex[:8]}"

    tools = build_tools_for_mode(["memory_upsert", "memory_search"], memory_repo=repo)
    upsert = next(t for t in tools if t.name == "memory_upsert")
    search = next(t for t in tools if t.name == "memory_search")

    out_up = await upsert.ainvoke(
        {
            "child_profile_id": child_id,
            "category": "hobby",
            "value_text": f"любит лего, маркер {marker}",
        }
    )
    print("upsert:", str(out_up)[:120])

    found = await memory_impl.memory_search_text(repo, child_id, marker, limit=5)
    print("search:", found[:200] if found else "(пусто)")

    if marker not in (found or ""):
        raise SystemExit("FAIL: маркер не найден в SQLite")
    print("OK: память 2.3 (без LLM)")


if __name__ == "__main__":
    asyncio.run(main())
