"""Интерактивный текстовый цикл: stdin → coordinator → stdout (без ASR/TTS)."""

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
from center_voice_agent.agent.gateway import AgentGateway
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.db.session import init_database
from center_voice_agent.logging_setup import bind_turn_context, new_correlation_id, setup_logging
from center_voice_agent.orchestration.coordinator import SessionCoordinator
from center_voice_agent.settings import get_settings


async def main() -> None:
    settings = get_settings()
    setup_logging(json_logs=settings.log_json, level=settings.log_level)
    sid = f"text-{uuid.uuid4().hex[:8]}"
    structlog.contextvars.bind_contextvars(**bind_turn_context(correlation_id=new_correlation_id(), session_id=sid))

    await init_database(settings.project_root, settings.database_url)
    use_live = bool(settings.llm_api_key) and "--live" in sys.argv
    llm = None if use_live else StaticChatModel(responses=["Поняла.", "Хорошо, продолжаем."])
    gateway = AgentGateway(settings=settings, llm=llm)
    coord = SessionCoordinator(gateway, settings=settings)
    stm = ShortTermMemory(max_turns=15)

    print("Текстовый чат (exit / выход). Режим:", "live LLM" if use_live else "fake LLM")
    while True:
        try:
            line = input("Вы: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line or line.lower() in {"exit", "выход", "quit"}:
            break
        r = await coord.handle_user_turn(
            session_id=sid,
            child_profile_id="child-text-1",
            user_text=line,
            short_term=stm,
            age_band="5-6",
        )
        print("Арина:", r.text)
        if r.mode_changed:
            print(f"  [режим: {r.previous_mode_id} -> {r.mode_id}]")

    await gateway.aclose()


if __name__ == "__main__":
    asyncio.run(main())
