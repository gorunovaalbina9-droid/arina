"""Проверка окружения: Python, .env, БД, режимы, тесты (опционально)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []

    ver = sys.version_info
    print(f"Python: {ver.major}.{ver.minor}.{ver.micro}")
    if ver >= (3, 14):
        warnings.append("Рекомендуется Python 3.11 или 3.12 (см. .python-version).")
    elif ver < (3, 11):
        errors.append("Нужен Python >= 3.11")

    env_path = REPO_ROOT / ".env"
    example = REPO_ROOT / ".env.example"
    if not env_path.is_file():
        errors.append(f"Нет файла .env — скопируйте: copy {example.name} .env")
    else:
        print(f"OK: .env найден ({env_path})")

    try:
        from center_voice_agent.settings import get_settings

        get_settings.cache_clear()
        s = get_settings()
        print(f"OK: settings (БД: {s.database_url[:60]}...)")
        if not s.llm_api_key or str(s.llm_api_key).startswith("replace"):
            warnings.append("LLM_API_KEY не задан — demo_turn OK, live_turn не заработает.")
        else:
            print("OK: LLM_API_KEY задан")
    except Exception as e:
        errors.append(f"settings: {e}")

    try:
        import asyncio
        from center_voice_agent.db.session import init_database
        from center_voice_agent.settings import get_settings

        s = get_settings()

        async def _init() -> None:
            await init_database(s.project_root, s.database_url)

        asyncio.run(_init())
        print("OK: init_db (миграции)")
    except Exception as e:
        errors.append(f"init_db: {e}")

    try:
        from center_voice_agent.modes.registry import ModeRegistry
        from center_voice_agent.settings import get_settings

        s = get_settings()
        reg = ModeRegistry(s.modes_dir, project_root=s.project_root, database_url=s.database_url)
        ids = reg.reload_all()
        print(f"OK: режимы {', '.join(ids)}")
    except Exception as e:
        errors.append(f"режимы: {e}")

    for w in warnings:
        print(f"ПРЕДУПРЕЖДЕНИЕ: {w}")
    if errors:
        print("\nОШИБКИ:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("\nПроверка пройдена. Дальше: python -m center_voice_agent.cli.demo_turn")
    print("С реальным API: python -m center_voice_agent.cli.live_turn Привет!")


if __name__ == "__main__":
    main()
