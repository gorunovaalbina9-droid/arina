"""
Блок 2 без готовой модели: всё, что не требует API.

  python -m center_voice_agent.cli.block2_offline

Проверяет: БД, режимы, demo_turn (fake LLM + логи), memory_roundtrip, plan B в коде.
После появления модели: live_turn и live_acceptance.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import structlog

from center_voice_agent.agent.fake_llm import StaticChatModel
from center_voice_agent.composition.container import AppContainer
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.db.session import init_database
from center_voice_agent.logging_setup import bind_turn_context, new_correlation_id, setup_logging
from center_voice_agent.settings import get_settings


def _header(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


async def main() -> None:
    settings = get_settings()
    setup_logging(json_logs=settings.log_json, level=settings.log_level)
    failures: list[str] = []

    _header("Блок 2 offline — без реального LLM")

    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        print(f"OK: .env есть ({env_path})")
    else:
        print("ПРЕДУПРЕЖДЕНИЕ: нет .env — скопируйте .env.example перед live API")
        print("       copy .env.example .env")

    _header("Инициализация БД")
    try:
        await init_database(settings.project_root, settings.database_url)
        print("OK: init_db / миграции")
    except Exception as exc:
        failures.append(f"init_db: {exc}")
        print(f"FAIL: {exc}")

    _header("Режимы YAML")
    try:
        from center_voice_agent.modes.registry import ModeRegistry

        reg = ModeRegistry(
            settings.modes_dir,
            project_root=settings.project_root,
            database_url=settings.database_url,
        )
        ids = reg.reload_all()
        print(f"OK: режимы: {', '.join(ids)}")
    except Exception as exc:
        failures.append(f"modes: {exc}")
        print(f"FAIL: {exc}")

    _header("2.3 memory_roundtrip (память без LLM)")
    try:
        from center_voice_agent.db.session import create_engine_and_session_factory
        from center_voice_agent.memory.repository import LongTermMemoryRepository
        from center_voice_agent.tools.factory import build_tools_for_mode

        _, session_factory = create_engine_and_session_factory(settings.database_url)
        repo = LongTermMemoryRepository(session_factory)
        child_id = f"child-offline-{uuid.uuid4().hex[:6]}"
        marker = f"offline-{uuid.uuid4().hex[:8]}"
        tools = build_tools_for_mode(
            ["memory_upsert", "memory_search"],
            memory_repo=repo,
            child_profile_id=child_id,
        )
        await tools[0].ainvoke(
            {"category": "hobby", "value_text": f"маркер {marker}", "child_profile_id": "hacker"}
        )
        found = await repo.search(child_id, marker, limit=5)
        if marker not in (found or ""):
            raise RuntimeError("маркер не найден после upsert")
        if "hacker" in (await repo.search("hacker", marker, limit=1) or ""):
            raise RuntimeError("session-bound failed")
        print(f"OK: upsert -> SQLite -> search (child={child_id})")
    except Exception as exc:
        failures.append(f"memory: {exc}")
        print(f"FAIL: {exc}")

    _header("2.4 demo_turn + логи (fake LLM)")
    correlation_id = new_correlation_id()
    sid = f"offline-{uuid.uuid4().hex[:8]}"
    structlog.contextvars.bind_contextvars(
        **bind_turn_context(correlation_id=correlation_id, session_id=sid)
    )
    try:
        container = AppContainer.from_settings(settings)
        coord = container.build_coordinator(
            llm=StaticChatModel(responses=["Привет! Я наставник. Всё хорошо."])
        )
        stm = ShortTermMemory(max_turns=settings.short_term_max_messages)
        result = await coord.handle_user_turn(
            session_id=sid,
            child_profile_id="child-offline-demo",
            user_text="Привет!",
            short_term=stm,
            age_band="5-6",
        )
        await coord.gateway.aclose()
        if not (result.text or "").strip():
            raise RuntimeError("пустой ответ demo_turn")
        print(f"OK: demo_turn, ответ: {(result.text or '')[:80]}...")
        print(f"OK: correlation_id={correlation_id} (см. gateway_in/out в JSON выше)")
    except Exception as exc:
        failures.append(f"demo_turn: {exc}")
        print(f"FAIL: {exc}")

    log_example = REPO_ROOT / "docs" / "log_example_gateway.jsonl"
    if log_example.is_file():
        print(f"OK: эталон логов {log_example.relative_to(REPO_ROOT)}")
    else:
        failures.append("нет log_example_gateway.jsonl")

    _header("2.5 Plan B (код)")
    fb = REPO_ROOT / "src" / "center_voice_agent" / "agent" / "text_tool_fallback.py"
    if fb.is_file() and settings.text_tool_fallback:
        print("OK: TEXT_TOOL_FALLBACK и text_tool_fallback.py")
    else:
        print("ПРЕДУПРЕЖДЕНИЕ: проверьте TEXT_TOOL_FALLBACK в .env")

    _header("Ждёт модель и API (не проверялось)")
    pending = [
        "2.2.1 Заполнить .env: LLM_API_KEY, LLM_BASE_URL, LLM_MODEL",
        "2.2.2 Баланс / квота API",
        "2.2.4 python -m center_voice_agent.cli.live_turn Привет!",
        "2.2.5 python -m center_voice_agent.cli.live_acceptance",
        "2.2.6–2.2.7 Память и plan B с реальным LLM",
    ]
    for line in pending:
        print(f"  • {line}")

    _header("Итог")
    if failures:
        print("OFFLINE FAIL:")
        for f in failures:
            print(f"  - {f}")
        get_settings.cache_clear()
        raise SystemExit(1)
    print("OFFLINE OK: всё без API готово. После модели — live_acceptance.")
    get_settings.cache_clear()
    raise SystemExit(0)


if __name__ == "__main__":
    asyncio.run(main())
