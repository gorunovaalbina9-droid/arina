"""Rate limit через Redis (shared между инстансами)."""

from __future__ import annotations

import time
from typing import Optional

import structlog

log = structlog.get_logger(__name__)

_WINDOW_MINUTE = 60
_WINDOW_HOUR = 3600


class RedisRateLimiter:
    def __init__(self, redis_url: str) -> None:
        try:
            import redis
        except ImportError as exc:
            raise RuntimeError(
                "Для RATE_LIMIT_BACKEND=redis установите: pip install center-voice-agent[redis]"
            ) from exc
        self._client = redis.from_url(redis_url, decode_responses=True)
        self._client.ping()

    def check(
        self,
        session_id: str,
        *,
        per_minute: int,
        per_hour: int,
    ) -> Optional[str]:
        now = int(time.time())
        key_m = f"rl:{session_id}:m"
        key_h = f"rl:{session_id}:h"
        pipe = self._client.pipeline()
        pipe.zremrangebyscore(key_m, 0, now - _WINDOW_MINUTE)
        pipe.zadd(key_m, {str(now): now})
        pipe.expire(key_m, _WINDOW_MINUTE + 5)
        pipe.zcard(key_m)
        pipe.zremrangebyscore(key_h, 0, now - _WINDOW_HOUR)
        pipe.zadd(key_h, {str(now): now})
        pipe.expire(key_h, _WINDOW_HOUR + 60)
        pipe.zcard(key_h)
        _, _, _, in_minute, _, _, in_hour = pipe.execute()
        if in_minute > per_minute:
            return f"rate_limit:minute:{in_minute}>{per_minute}"
        if in_hour > per_hour:
            return f"rate_limit:hour:{in_hour}>{per_hour}"
        return None

    def reset(self) -> None:
        """Только для тестов — удаляет ключи rl:* (осторожно в prod)."""
        for key in self._client.scan_iter("rl:*"):
            self._client.delete(key)
