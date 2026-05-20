"""Создать child_profile в SQLite (оболочка для агента)."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from center_voice_agent.db.session import create_engine_and_session_factory, init_database
from center_voice_agent.memory.repository import LongTermMemoryRepository
from center_voice_agent.settings import get_settings


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("child_id", help="UUID или произвольный id профиля")
    parser.add_argument("--center-id", default="default-center")
    parser.add_argument("--age-band", default=None)
    args = parser.parse_args()

    settings = get_settings()
    await init_database(settings.project_root, settings.database_url)
    engine, factory = create_engine_and_session_factory(settings.database_url)
    repo = LongTermMemoryRepository(factory)
    await repo.ensure_child_profile(args.child_id, center_id=args.center_id)
    await engine.dispose()
    print(f"OK child_profile_id={args.child_id} center_id={args.center_id} age_band={args.age_band or '-'}")


if __name__ == "__main__":
    asyncio.run(main())
