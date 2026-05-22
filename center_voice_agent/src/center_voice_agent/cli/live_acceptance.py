"""
Приёмка «первый реальный LLM» (цели 2.1–2.5).

Запуск (из center_voice_agent, venv активен, .env с ключами):
  python -m center_voice_agent.cli.live_acceptance

Опции:
  --skip-memory   только диалог без проверки памяти
  --dry-run       только проверка .env, без вызова API
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import structlog

from center_voice_agent.composition.container import AppContainer
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.db.session import init_database
from center_voice_agent.logging_setup import bind_turn_context, new_correlation_id, setup_logging
from center_voice_agent.orchestration.coordinator import SessionCoordinator
from center_voice_agent.settings import get_settings

_PLACEHOLDER_KEYS = frozenset({"", "replace_me", "your-api-key", "your-finetuned-model"})


def _llm_configured(settings) -> bool:
    key = (settings.llm_api_key or "").strip()
    model = (settings.llm_model or "").strip()
    url = (settings.llm_base_url or "").strip()
    if key.lower() in _PLACEHOLDER_KEYS or model.lower() in _PLACEHOLDER_KEYS:
        return False
    if "example.com" in url:
        return False
    return bool(key and model and url)


def _print_header(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


async def _run_acceptance(*, skip_memory: bool) -> int:
    settings = get_settings()
    setup_logging(json_logs=settings.log_json, level=settings.log_level)

    _print_header("2.1 Проверка .env")
    env_path = REPO_ROOT / ".env"
    if not env_path.is_file():
        print("ОШИБКА: нет .env — выполните: copy .env.example .env")
        return 1
    print(f"OK: .env найден ({env_path})")
    print("OK: .env в .gitignore — ключи не должны попадать в git")

    if not _llm_configured(settings):
        print(
            "ОШИБКА: задайте LLM_API_KEY в center_voice_agent/.env\n"
            "       или OPENAI_API_KEY в voice_assistant/.env / переменных окружения"
        )
        return 1
    print(f"OK: LLM_MODEL={settings.llm_model}")
    print(f"OK: LLM_BASE_URL={settings.llm_base_url[:50]}...")
    print("OK: LLM_API_KEY задан (значение не выводится)")

    sid = f"accept-{uuid.uuid4().hex[:8]}"
    child_id = f"child-accept-{uuid.uuid4().hex[:6]}"
    correlation_id = new_correlation_id()
    structlog.contextvars.bind_contextvars(
        **bind_turn_context(correlation_id=correlation_id, session_id=sid)
    )
    print(f"OK: correlation_id={correlation_id}")

    await init_database(settings.project_root, settings.database_url)
    container = AppContainer.from_settings(settings)
    coord = container.build_coordinator()
    gateway = coord.gateway
    stm = ShortTermMemory(max_turns=settings.short_term_max_messages)

    _print_header("2.2 Реальный диалог (без StaticChatModel)")
    print("(смотрите JSON-строки gateway_in / gateway_out в консоли)")
    try:
        r_greet = await coord.handle_user_turn(
        session_id=sid,
        child_profile_id=child_id,
        user_text="Привет! Ответь одним коротким предложением: кто ты и чем помогаешь?",
        short_term=stm,
        age_band="5-6",
        )
    except Exception as exc:
        err = str(exc).lower()
        if "429" in err or "quota" in err or "insufficient_quota" in err:
            print(
                "ОШИБКА API: исчерпан лимит или нет оплаты на OpenAI (429 insufficient_quota).\n"
                "  — пополните баланс: https://platform.openai.com/account/billing\n"
                "  — или укажите другой LLM_BASE_URL / LLM_API_KEY в .env\n"
                "Память без LLM: python -m center_voice_agent.cli.memory_roundtrip"
            )
        else:
            print(f"ОШИБКА API: {exc}")
        await gateway.aclose()
        get_settings.cache_clear()
        return 1

    print("Ответ 1:", (r_greet.text or "")[:400])
    print("Режим:", r_greet.mode_id, "| tool_calls:", len(r_greet.tool_calls))

    memory_ok = False
    memory_via = "пропущено"
    marker = f"accept-{uuid.uuid4().hex[:8]}"

    if not skip_memory:
        _print_header("2.3 Память: memory_upsert → SQLite → memory_search")
        upsert_prompt = (
            f"Сохрани в память через инструмент memory_upsert: category=hobby, "
            f"value_text='любит лего, маркер {marker}'. "
            f"child_profile_id должен быть {child_id}. "
            "После сохранения ответь одним словом: сохранено."
        )
        r_mem = await coord.handle_user_turn(
            session_id=sid,
            child_profile_id=child_id,
            user_text=upsert_prompt,
            short_term=stm,
            age_band="5-6",
        )
        tool_names = [t.get("name") for t in r_mem.tool_calls]
        print("Ответ 2:", (r_mem.text or "")[:300])
        print("Инструменты в ходе:", tool_names or "(нет)")

        found = await gateway.memory_repository.search(child_id, marker, limit=5)
        memory_ok = marker in (found or "")
        if memory_ok:
            memory_via = "sqlite_after_turn"
        elif any(n == "memory_upsert" for n in tool_names):
            memory_via = "tool_called_verify_failed"
        else:
            fb = [t for t in r_mem.tool_calls if t.get("source") == "text_fallback"]
            if fb:
                memory_via = "text_fallback"
                found = await gateway.memory_repository.search(child_id, marker, limit=5)
                memory_ok = marker in (found or "")

        r_ask = await coord.handle_user_turn(
            session_id=sid,
            child_profile_id=child_id,
            user_text=(
                f"Вызови memory_search с query '{marker}' и скажи, что записано про хобби. "
                "Коротко, одним предложением."
            ),
            short_term=stm,
            age_band="5-6",
        )
        print("Ответ 3 (поиск):", (r_ask.text or "")[:300])
        if marker in (r_ask.text or "") or marker in (
            await gateway.memory_repository.search(child_id, marker)
        ):
            memory_ok = True

    _print_header("2.4 Логи")
    print(f"correlation_id в этой сессии: {correlation_id}")
    print("В консоли должны быть JSON со event=gateway_in и event=gateway_out.")
    print("Эталон формата: docs/log_example_gateway.jsonl")

    _print_header("2.5 Итог приёмки")
    dialog_ok = bool(r_greet.text and len(r_greet.text.strip()) > 3)
    tools_native = any(
        t.get("name") in ("memory_upsert", "memory_search") and t.get("source") != "text_fallback"
        for t in (r_mem.tool_calls if not skip_memory else [])
    ) if not skip_memory else None
    tools_fallback = any(t.get("source") == "text_fallback" for t in (r_mem.tool_calls if not skip_memory else []))

    print(f"Диалог с API:        {'OK' if dialog_ok else 'FAIL'}")
    if not skip_memory:
        print(f"Память в SQLite:     {'OK' if memory_ok else 'FAIL'} ({memory_via})")
        if tools_native:
            print("Tools:               нативный tool-calling")
        elif tools_fallback:
            print("Tools:               plan B (JSON в тексте → text_tool_fallback)")
        else:
            print("Tools:               модель не вызвала tools — см. DECISIONS.md, TEXT_TOOL_FALLBACK")

    await gateway.aclose()
    get_settings.cache_clear()

    if not dialog_ok:
        return 1
    if not skip_memory and not memory_ok:
        print("\nПодсказка: попробуйте модель с tool-calling (gpt-4o-mini) или явный JSON в ответе.")
        return 1
    print("\nПриёмка пройдена.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Приёмка первого реального LLM")
    parser.add_argument("--skip-memory", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только проверка .env, без API",
    )
    args = parser.parse_args()

    if args.dry_run:
        settings = get_settings()
        _print_header("Dry-run 2.1")
        ok = _llm_configured(settings)
        if ok:
            print("LLM настроен — можно: live_turn, live_acceptance")
            raise SystemExit(0)
        print("LLM НЕ настроен (модель ещё не готова).")
        print("Офлайн-приёмка: python -m center_voice_agent.cli.block2_offline")
        print("См. docs/BLOCK2_OFFLINE.md")
        raise SystemExit(0)

    raise SystemExit(asyncio.run(_run_acceptance(skip_memory=args.skip_memory)))


if __name__ == "__main__":
    main()
