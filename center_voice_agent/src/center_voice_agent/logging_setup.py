from __future__ import annotations

import logging
import sys
import uuid
from typing import Any, Mapping, Optional

import structlog


def setup_logging(*, json_logs: bool, level: str) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        timestamper,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        formatter = structlog.processors.JSONRenderer()
    else:
        formatter = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=shared + [formatter],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))


def new_correlation_id() -> str:
    return str(uuid.uuid4())


def bind_turn_context(
    *,
    correlation_id: str,
    session_id: str,
    mode_id: Optional[str] = None,
    scenario_id: Optional[str] = None,
    node_id: Optional[str] = None,
    child_profile_id: Optional[str] = None,
) -> Mapping[str, Any]:
    ctx: dict[str, Any] = {
        "correlation_id": correlation_id,
        "session_id": session_id,
    }
    if mode_id is not None:
        ctx["mode_id"] = mode_id
    if scenario_id is not None:
        ctx["scenario_id"] = scenario_id
    if node_id is not None:
        ctx["scenario_node_id"] = node_id
    if child_profile_id is not None:
        ctx["child_profile_id"] = child_profile_id
    return ctx
