from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from center_voice_agent.logging_setup import setup_logging
from center_voice_agent.modes.registry import ModeRegistry
from center_voice_agent.settings import get_settings


def main() -> None:
    settings = get_settings()
    setup_logging(json_logs=settings.log_json, level=settings.log_level)
    reg = ModeRegistry(
        settings.modes_dir,
        project_root=settings.project_root,
        database_url=settings.database_url,
        modes_source=settings.modes_source,
        modes_center_id=settings.modes_center_id,
    )
    ids = reg.reload_all()
    print("OK:", ", ".join(ids))


if __name__ == "__main__":
    main()
