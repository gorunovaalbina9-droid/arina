from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from center_voice_agent.admin.publish import publish_mode_yaml
from center_voice_agent.composition.reload import reload_process_catalog
from center_voice_agent.composition.runtime import get_process_container
from center_voice_agent.logging_setup import setup_logging
from center_voice_agent.settings import get_settings


async def _publish_async(
    *,
    raw: str,
    mode_id: str,
    center_id: str | None,
    status: str,
) -> str:
    container = await get_process_container()
    return await publish_mode_yaml(
        container.engine,
        config_yaml=raw,
        mode_id=mode_id,
        center_id=center_id,
        status=status,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Записать YAML режима в SQLite (таблица mode_definitions). Нужны применённые миграции (init_db).",
    )
    parser.add_argument("yaml_path", type=Path, help="Путь к YAML режима")
    parser.add_argument("--mode-id", dest="mode_id", default=None, help="Иначе берётся поле id из YAML")
    parser.add_argument("--center-id", dest="center_id", default=None)
    parser.add_argument("--draft", action="store_true", help="Статус draft вместо published")
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(json_logs=settings.log_json, level=settings.log_level)

    path = args.yaml_path
    if not path.is_file():
        raise SystemExit(f"Файл не найден: {path}")

    raw = path.read_text(encoding="utf-8-sig")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise SystemExit("YAML должен быть одним объектом с полями режима")
    mid = args.mode_id or data.get("id")
    if not mid:
        raise SystemExit("Укажите id в YAML или флаг --mode-id")
    status = "draft" if args.draft else "published"
    rid = asyncio.run(
        _publish_async(
            raw=raw,
            mode_id=str(mid),
            center_id=args.center_id,
            status=status,
        )
    )

    async def _reload() -> None:
        await reload_process_catalog()

    asyncio.run(_reload())
    print(f"OK row_id={rid} mode_id={mid} status={status}")


if __name__ == "__main__":
    main()
