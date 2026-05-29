"""Rate limit по session_id (v1 in-memory; Redis — отдельная реализация)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional, Protocol

_WINDOW_MINUTE = 60.0
_WINDOW_HOUR = 3600.0


class RateLimiter(Protocol):
    def check(
        self,
        session_id: str,
        *,
        per_minute: int,
        per_hour: int,
    ) -> Optional[str]:
        """None если ок, иначе reason для security_incident."""
        ...


def _prune(ts: Deque[float], *, older_than: float) -> None:
    cutoff = time.monotonic() - older_than
    while ts and ts[0] < cutoff:
        ts.popleft()


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: Dict[str, Deque[float]] = defaultdict(deque)

    def check(
        self,
        session_id: str,
        *,
        per_minute: int,
        per_hour: int,
    ) -> Optional[str]:
        now = time.monotonic()
        bucket = self._buckets[session_id]
        bucket.append(now)
        _prune(bucket, older_than=_WINDOW_HOUR)

        minute_cut = now - _WINDOW_MINUTE
        in_minute = sum(1 for t in bucket if t >= minute_cut)
        in_hour = len(bucket)

        if in_minute > per_minute:
            return f"rate_limit:minute:{in_minute}>{per_minute}"
        if in_hour > per_hour:
            return f"rate_limit:hour:{in_hour}>{per_hour}"
        return None

    def reset(self) -> None:
        self._buckets.clear()


_default_limiter = InMemoryRateLimiter()


def get_default_rate_limiter() -> InMemoryRateLimiter:
    return _default_limiter


def check_rate_limit(
    session_id: str,
    *,
    per_minute: int,
    per_hour: int,
    limiter: Optional[InMemoryRateLimiter] = None,
) -> Optional[str]:
    lim = limiter or _default_limiter
    return lim.check(session_id, per_minute=per_minute, per_hour=per_hour)


def reset_rate_limit_for_tests() -> None:
    _default_limiter.reset()
