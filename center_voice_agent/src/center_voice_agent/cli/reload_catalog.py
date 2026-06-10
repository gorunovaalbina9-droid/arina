"""CLI: reload modes + scenario scan в long-running процессе (или standalone)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from center_voice_agent.composition.reload import reload_process_catalog
from center_voice_agent.logging_setup import setup_logging
from center_voice_agent.settings import get_settings


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Reload modes + scenario scan cache")
    parser.add_argument(
        "--clear-settings",
        action="store_true",
        help="Сбросить get_settings() cache после правки .env",
    )
    args = parser.parse_args()
    settings = get_settings()
    setup_logging(json_logs=settings.log_json, level=settings.log_level)

    async def _run():
        result = await reload_process_catalog(clear_settings_cache=args.clear_settings)
        if result is None:
            return
        print("OK modes:", ", ".join(result.mode_ids))
        print("OK scenarios:", ", ".join(result.scenario_ids))

    asyncio.run(_run())


if __name__ == "__main__":
    main()
