from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from center_voice_agent.logging_setup import setup_logging
from center_voice_agent.modes.db_source import publish_mode_yaml_sync
from center_voice_agent.settings import get_settings


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
    rid = publish_mode_yaml_sync(
        settings.database_url,
        config_yaml=raw,
        mode_id=str(mid),
        center_id=args.center_id,
        status=status,
    )
    print(f"OK row_id={rid} mode_id={mid} status={status}")


if __name__ == "__main__":
    main()
