"""Фабрика rate limiter: memory | redis."""

from __future__ import annotations

from typing import Literal

import structlog

from center_voice_agent.security.rate_limit import InMemoryRateLimiter, RateLimiter
from center_voice_agent.settings import Settings

log = structlog.get_logger(__name__)


def build_rate_limiter(settings: Settings) -> RateLimiter:
    backend: Literal["memory", "redis"] = settings.rate_limit_backend
    if backend == "redis":
        if not settings.redis_url:
            log.warning("rate_limit_redis_no_url", fallback="memory")
            return InMemoryRateLimiter()
        try:
            from center_voice_agent.security.rate_limit_redis import RedisRateLimiter

            return RedisRateLimiter(settings.redis_url)
        except Exception as exc:
            log.warning("rate_limit_redis_init_failed", error=str(exc)[:200], fallback="memory")
            return InMemoryRateLimiter()
    return InMemoryRateLimiter()
