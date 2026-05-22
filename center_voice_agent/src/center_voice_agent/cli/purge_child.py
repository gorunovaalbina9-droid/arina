"""Удаление данных child_profile (память, сессии, профиль) — пилот 12.2.2."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sqlalchemy import text

from center_voice_agent.db.session import create_engine_and_session_factory, init_database
from center_voice_agent.settings import get_settings


async def purge_child(child_profile_id: str, *, confirm: bool) -> None:
    settings = get_settings()
    await init_database(settings.project_root, settings.database_url)
    engine, factory = create_engine_and_session_factory(settings.database_url)

    async with factory() as session:
        mem = await session.execute(
            text(
                "SELECT COUNT(*) FROM long_term_memory_entries WHERE child_profile_id = :id"
            ),
            {"id": child_profile_id},
        )
        mem_n = int(mem.scalar_one())
        sess = await session.execute(
            text("SELECT COUNT(*) FROM session_state WHERE child_profile_id = :id"),
            {"id": child_profile_id},
        )
        sess_n = int(sess.scalar_one())

        if not confirm:
            print(f"Будет удалено: memory={mem_n}, sessions={sess_n}, profile=1")
            print("Повторите с --confirm")
            await engine.dispose()
            raise SystemExit(2)

        await session.execute(
            text("DELETE FROM session_state WHERE child_profile_id = :id"),
            {"id": child_profile_id},
        )
        await session.execute(
            text("DELETE FROM long_term_memory_entries WHERE child_profile_id = :id"),
            {"id": child_profile_id},
        )
        await session.execute(
            text("DELETE FROM child_profiles WHERE id = :id"),
            {"id": child_profile_id},
        )
        await session.commit()

    await engine.dispose()
    print(f"OK: удалён child_profile_id={child_profile_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Удалить ПДн ребёнка из SQLite")
    parser.add_argument("child_id", help="child_profile_id")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Выполнить удаление (без флага — только превью)",
    )
    args = parser.parse_args()
    asyncio.run(purge_child(args.child_id, confirm=args.confirm))


if __name__ == "__main__":
    main()
