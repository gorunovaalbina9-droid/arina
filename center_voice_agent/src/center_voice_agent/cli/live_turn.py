"""Один ход с реальным LLM (нужен LLM_API_KEY в .env)."""

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

from center_voice_agent.agent.gateway import AgentGateway
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.db.session import init_database
from center_voice_agent.logging_setup import bind_turn_context, new_correlation_id, setup_logging
from center_voice_agent.orchestration.coordinator import SessionCoordinator
from center_voice_agent.settings import get_settings


async def main() -> None:
    settings = get_settings()
    setup_logging(json_logs=settings.log_json, level=settings.log_level)
    if not settings.llm_api_key or str(settings.llm_api_key).strip().lower() in (
        "",
        "replace_me",
        "your-api-key",
    ):
        raise SystemExit(
            "Нет LLM_API_KEY в center_voice_agent/.env\n"
            "1) copy .env.example .env\n"
            "2) Впишите LLM_API_KEY, LLM_BASE_URL, LLM_MODEL\n"
            "3) python -m center_voice_agent.cli.setup_check"
        )

    sid = f"live-{uuid.uuid4().hex[:8]}"
    structlog.contextvars.bind_contextvars(**bind_turn_context(correlation_id=new_correlation_id(), session_id=sid))

    await init_database(settings.project_root, settings.database_url)
    gateway = AgentGateway(settings=settings)
    coord = SessionCoordinator(gateway, settings=settings)
    stm = ShortTermMemory(max_turns=15)

    user = " ".join(sys.argv[1:]).strip() or "Привет! Расскажи коротко, чем ты можешь помочь."
    result = await coord.handle_user_turn(
        session_id=sid,
        child_profile_id="child-live-1",
        user_text=user,
        short_term=stm,
        age_band="5-6",
    )
    print(result.text)
    await gateway.aclose()


if __name__ == "__main__":
    asyncio.run(main())
