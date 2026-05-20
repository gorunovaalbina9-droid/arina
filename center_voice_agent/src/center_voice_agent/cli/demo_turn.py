from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

# .../center_voice_agent/src/center_voice_agent/cli/demo_turn.py → корень репозитория
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
from center_voice_agent.scenarios.graph_engine import load_scenario
from center_voice_agent.settings import get_settings


async def main() -> None:
    parser = argparse.ArgumentParser(description="Демо-диалог (fake LLM или --live с реальным API)")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Реальный ChatOpenAI из .env / OPENAI_API_KEY (без StaticChatModel)",
    )
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(json_logs=settings.log_json, level=settings.log_level)

    if args.live and not (settings.llm_api_key or "").strip():
        raise SystemExit("Для --live нужен LLM_API_KEY или OPENAI_API_KEY")

    sid = f"demo-{uuid.uuid4().hex[:10]}"
    correlation_id = new_correlation_id()
    structlog.contextvars.bind_contextvars(**bind_turn_context(correlation_id=correlation_id, session_id=sid))

    await init_database(settings.project_root, settings.database_url)

    llm = None if args.live else StaticChatModel(
        responses=[
            "Привет! Я наставник центра. Как настроение?",
            "Рада слышать. Уточни: что сегодня было самым интересным?",
            "Продолжаем в учебном режиме.",
        ]
    )
    gateway = AgentGateway(settings=settings, llm=llm)
    coord = SessionCoordinator(gateway, settings=settings)

    stm = ShortTermMemory(max_turns=15)
    scenario_path = settings.scenarios_dir / "example_linear.yaml"
    if scenario_path.is_file():
        g = load_scenario(scenario_path)
        await gateway.session_repository.ensure(sid, "child-demo-1", default_mode_id=settings.default_mode_id)
        await gateway.session_repository.attach_scenario(sid, g.id)

    if not args.live:
        sw = await coord.handle_user_turn(
            session_id=sid,
            child_profile_id="child-demo-1",
            user_text="переключись в учебный",
            short_term=stm,
            age_band="5-6",
        )
        print("Смена режима:", sw.mode_changed, "->", sw.mode_id, "|", sw.text)

    r1 = await coord.handle_user_turn(
        session_id=sid,
        child_profile_id="child-demo-1",
        user_text="Привет!" if not args.live else "Привет! Ответь одним коротким предложением.",
        short_term=stm,
        long_term_summary=None if args.live else "Любит рисовать и кошек.",
        age_band="5-6",
    )
    print(r1.text)
    if not args.live:
        print("Узел сценария после 1-го хода:", r1.scenario_node_id)

    if not args.live:
        r2 = await coord.handle_user_turn(
            session_id=sid,
            child_profile_id="child-demo-1",
            user_text="Рисовал кота.",
            short_term=stm,
            age_band="5-6",
        )
        print(r2.text)
        print("Узел сценария после 2-го хода:", r2.scenario_node_id)

    await gateway.aclose()


if __name__ == "__main__":
    asyncio.run(main())
