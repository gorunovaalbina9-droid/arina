from __future__ import annotations

import hashlib
import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any, Mapping, Optional

import structlog

from center_voice_agent.settings import Settings


def _make_file_writer(path: Path, *, max_bytes: int) -> Any:
    path.parent.mkdir(parents=True, exist_ok=True)

    def _write(_logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        row = dict(event_dict)
        row["level"] = method_name
        line = json.dumps(row, ensure_ascii=False, default=str) + "\n"
        with path.open("a", encoding="utf-8") as f:
            f.write(line)
        if path.is_file() and path.stat().st_size > max_bytes:
            _trim_incidents_file(path, max_bytes=max_bytes)
        return event_dict

    return _write


def setup_logging(
    *,
    json_logs: bool,
    level: str,
    log_file: Optional[Path] = None,
    log_file_max_bytes: int = 5_000_000,
    log_file_backup_count: int = 3,
) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        timestamper,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    processors = list(shared)
    if log_file is not None:
        processors.append(_make_file_writer(log_file, max_bytes=log_file_max_bytes))
    processors.append(renderer)

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    _ = log_file_backup_count  # reserved for future RotatingFileHandler swap


def configure_logging(settings: Settings) -> None:
    """Единая точка: stdout и опционально logs/agent.log."""
    structlog.reset_defaults()
    log_file: Optional[Path] = None
    if settings.log_file_path:
        p = Path(settings.log_file_path)
        log_file = p if p.is_absolute() else settings.project_root / p
    setup_logging(
        json_logs=settings.log_json,
        level=settings.log_level,
        log_file=log_file,
        log_file_max_bytes=settings.log_file_max_bytes,
        log_file_backup_count=settings.log_file_backup_count,
    )


def new_correlation_id() -> str:
    return str(uuid.uuid4())


def text_fingerprint(text: str) -> str:
    """Короткий хэш текста для логов без хранения ПДн."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


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


def _trim_incidents_file(path: Path, *, max_bytes: int) -> None:
    if not path.is_file() or path.stat().st_size <= max_bytes:
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    keep: list[str] = []
    size = 0
    for line in reversed(lines):
        if not line.strip():
            continue
        size += len(line.encode("utf-8")) + 1
        if size > max_bytes:
            break
        keep.append(line)
    path.write_text("\n".join(reversed(keep)) + ("\n" if keep else ""), encoding="utf-8")


def log_security_incident(
    *,
    reason: str,
    session_id: str,
    child_profile_id: Optional[str] = None,
    direction: str = "input",
    incidents_file: Optional[Path] = None,
    incidents_max_bytes: int = 1_000_000,
) -> None:
    payload = {
        "event": "security_incident",
        "reason": reason,
        "session_id": session_id,
        "child_profile_id": child_profile_id,
        "direction": direction,
    }
    structlog.get_logger(__name__).warning(
        "security_incident",
        reason=reason,
        session_id=session_id,
        child_profile_id=child_profile_id,
        direction=direction,
    )
    path = incidents_file
    max_bytes = incidents_max_bytes
    if path is None:
        try:
            from center_voice_agent.settings import get_settings

            s = get_settings()
            if s.security_incidents_path:
                p = Path(s.security_incidents_path)
                path = p if p.is_absolute() else s.project_root / p
                max_bytes = s.security_incidents_max_bytes
        except Exception:
            return
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    _trim_incidents_file(path, max_bytes=max_bytes)
