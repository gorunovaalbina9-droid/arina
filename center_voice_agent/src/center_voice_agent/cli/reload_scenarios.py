"""Сброс кэша scan сценариев и список id из config/scenarios/."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from center_voice_agent.scenarios.loader import clear_scenario_scan_cache
from center_voice_agent.composition.reload import reload_process_catalog
from center_voice_agent.settings import get_settings


def main() -> None:
    import asyncio

    settings = get_settings()

    async def _run() -> None:
        result = await reload_process_catalog()
        if result is not None:
            print("OK:", ", ".join(result.scenario_ids))
        else:
            clear_scenario_scan_cache()
            root = settings.scenarios_dir
            ids: list[str] = []
            if root.is_dir():
                from center_voice_agent.scenarios.graph_engine import load_scenario

                for p in sorted(root.glob("*.yaml")):
                    g = load_scenario(p)
                    ids.append(g.id)
            print("OK:", ", ".join(sorted(set(ids))))

    asyncio.run(_run())


if __name__ == "__main__":
    main()
