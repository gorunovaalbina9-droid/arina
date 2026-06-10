"""Логирование метрик хода (вынесено из AgentGateway)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import structlog

from center_voice_agent.logging_setup import text_fingerprint
from center_voice_agent.settings import Settings

log = structlog.get_logger(__name__)


@dataclass
class TurnTimings:
    modes_resolve_ms: int = 0
    memory_prefetch_ms: int = 0
    llm_ms: int = 0
    total_ms: int = 0


def log_gateway_in(
    settings: Settings,
    *,
    session_id: str,
    child_profile_id: str,
    mode_id: str,
    user_text: str,
    scenario_id: Optional[str],
    scenario_node_id: Optional[str],
    age_band: Optional[str],
) -> None:
    gw_in: dict[str, Any] = {
        "session_id": session_id,
        "child_profile_id": child_profile_id,
        "mode_id": mode_id,
        "scenario_id": scenario_id,
        "scenario_node_id": scenario_node_id,
        "user_text_len": len(user_text),
        "age_band": age_band,
    }
    if settings.log_redact_user_text:
        gw_in["user_text_fp"] = text_fingerprint(user_text)
    else:
        gw_in["user_text"] = user_text
    log.info("gateway_in", **gw_in)


def log_modes_resolve(
    *,
    session_id: str,
    mode_id: str,
    display_name: str,
    tool_ids: list[str],
    modes_resolve_ms: int,
) -> None:
    log.info(
        "modes_resolve",
        session_id=session_id,
        mode_id=mode_id,
        display_name=display_name,
        tool_ids=tool_ids,
        modes_resolve_ms=modes_resolve_ms,
    )


def log_gateway_out(
    *,
    session_id: str,
    mode_id: str,
    scenario_id: Optional[str],
    scenario_node_id: Optional[str],
    reply_len: int,
    tool_calls: int,
    tool_rounds: int,
    timings: TurnTimings,
) -> None:
    log.info(
        "gateway_out",
        session_id=session_id,
        mode_id=mode_id,
        scenario_id=scenario_id,
        scenario_node_id=scenario_node_id,
        latency_ms=timings.total_ms,
        modes_resolve_ms=timings.modes_resolve_ms,
        memory_prefetch_ms=timings.memory_prefetch_ms,
        llm_ms=timings.llm_ms,
        llm_and_tools_ms=timings.llm_ms,
        reply_len=reply_len,
        tool_calls=tool_calls,
        tool_rounds=tool_rounds,
    )
