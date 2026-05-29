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

from center_voice_agent.admin.publish import publish_scenario_yaml
from center_voice_agent.composition.runtime import get_process_container
from center_voice_agent.logging_setup import setup_logging
from center_voice_agent.scenarios.loader import clear_scenario_scan_cache
from center_voice_agent.settings import get_settings


async def _publish_async(
    *,
    raw: str,
    scenario_id: str,
    center_id: str | None,
    status: str,
    subject: str | None,
    age_band: str | None,
) -> str:
    container = await get_process_container()
    return await publish_scenario_yaml(
        container.engine,
        config_yaml=raw,
        scenario_id=scenario_id,
        center_id=center_id,
        status=status,
        subject=subject,
        age_band=age_band,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Публикация YAML сценария в SQLite (таблица scenario_publish). Нужны миграции (init_db).",
    )
    parser.add_argument("yaml_path", type=Path, help="Путь к YAML графа сценария")
    parser.add_argument("--scenario-id", dest="scenario_id", default=None, help="Иначе берётся поле id из YAML")
    parser.add_argument("--center-id", dest="center_id", default=None)
    parser.add_argument("--subject", dest="subject", default=None)
    parser.add_argument("--age-band", dest="age_band", default=None)
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
        raise SystemExit("YAML должен быть одним объектом с полями графа")
    sid = args.scenario_id or data.get("id")
    if not sid:
        raise SystemExit("Укажите id в YAML или флаг --scenario-id")
    status = "draft" if args.draft else "published"
    rid = asyncio.run(
        _publish_async(
            raw=raw,
            scenario_id=str(sid),
            center_id=args.center_id,
            status=status,
            subject=args.subject,
            age_band=args.age_band,
        )
    )
    clear_scenario_scan_cache()
    print(f"OK row_id={rid} scenario_id={sid} status={status}")


if __name__ == "__main__":
    main()
