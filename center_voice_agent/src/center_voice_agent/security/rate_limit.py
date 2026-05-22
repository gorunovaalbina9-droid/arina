"""In-memory rate limit по session_id (v1, без Redis)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

_WINDOW_MINUTE = 60.0
_WINDOW_HOUR = 3600.0
_buckets: Dict[str, Deque[float]] = defaultdict(deque)


def _prune(ts: Deque[float], *, older_than: float) -> None:
    cutoff = time.monotonic() - older_than
    while ts and ts[0] < cutoff:
        ts.popleft()


def check_rate_limit(
    session_id: str,
    *,
    per_minute: int,
    per_hour: int,
) -> Optional[str]:
    """None если ок, иначе reason для security_incident."""
    now = time.monotonic()
    bucket = _buckets[session_id]
    bucket.append(now)
    _prune(bucket, older_than=_WINDOW_HOUR)

    minute_cut = now - _WINDOW_MINUTE
    hour_cut = now - _WINDOW_HOUR
    in_minute = sum(1 for t in bucket if t >= minute_cut)
    in_hour = len(bucket)

    if in_minute > per_minute:
        return f"rate_limit:minute:{in_minute}>{per_minute}"
    if in_hour > per_hour:
        return f"rate_limit:hour:{in_hour}>{per_hour}"
    return None


def reset_rate_limit_for_tests() -> None:
    """Очистка buckets между тестами."""
    _buckets.clear()
