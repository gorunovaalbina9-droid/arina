from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from center_voice_agent.db.session import init_database
from center_voice_agent.logging_setup import setup_logging
from center_voice_agent.settings import get_settings


async def main() -> None:
    settings = get_settings()
    setup_logging(json_logs=settings.log_json, level=settings.log_level)
    await init_database(settings.project_root, settings.database_url)
    print("Миграции применены:", settings.database_url)


if __name__ == "__main__":
    asyncio.run(main())
