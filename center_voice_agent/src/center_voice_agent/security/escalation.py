"""Эскалация повторных инцидентов модерации педагогу (лог + security_incidents)."""

from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque, Dict, Optional

import structlog

log = structlog.get_logger(__name__)

_WINDOW_SEC = 3600.0


@dataclass
class EscalationTracker:
    """In-process счётчик блокировок; для multi-instance — дублировать через Redis позже."""

    threshold: int = 3
    window_sec: float = _WINDOW_SEC
    _hits: Dict[str, Deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def record_block(
        self,
        *,
        session_id: str,
        child_profile_id: Optional[str],
        reason: str,
        direction: str,
    ) -> bool:
        key = child_profile_id or session_id
        now = time.monotonic()
        bucket = self._hits[key]
        bucket.append(now)
        cutoff = now - self.window_sec
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        count = len(bucket)
        if count < self.threshold:
            return False
        log.warning(
            "moderation_escalation",
            session_id=session_id,
            child_profile_id=child_profile_id,
            direction=direction,
            reason=reason,
            block_count=count,
            threshold=self.threshold,
            notify_pedagogue=True,
        )
        return True


_default_tracker = EscalationTracker()


def get_escalation_tracker(*, threshold: int = 3) -> EscalationTracker:
    global _default_tracker
    if _default_tracker.threshold != threshold:
        _default_tracker = EscalationTracker(threshold=threshold)
    return _default_tracker


def log_moderation_escalation(
    *,
    session_id: str,
    child_profile_id: Optional[str],
    reason: str,
    direction: str,
    block_count: int,
    incidents_file: Optional[Path] = None,
    incidents_max_bytes: int = 1_000_000,
) -> None:
    payload = {
        "event": "moderation_escalation",
        "session_id": session_id,
        "child_profile_id": child_profile_id,
        "reason": reason,
        "direction": direction,
        "block_count": block_count,
        "notify_pedagogue": True,
    }
    log.warning("moderation_escalation", **{k: v for k, v in payload.items() if k != "event"})
    if incidents_file is None:
        return
    incidents_file.parent.mkdir(parents=True, exist_ok=True)
    with incidents_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    from center_voice_agent.logging_setup import _trim_incidents_file

    _trim_incidents_file(incidents_file, max_bytes=incidents_max_bytes)
