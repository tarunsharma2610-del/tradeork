import time
from collections import defaultdict
from dataclasses import dataclass

from fastapi import HTTPException, Request, status
from redis.asyncio import Redis

from app.core.config import settings
from app.core.redis import get_redis_client

_memory: dict[str, list[float]] = defaultdict(list)


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after: int
    limit: int
    remaining: int


class RateLimiter:
    """Fixed-window rate limiter backed by Redis with an in-memory fallback.

    The in-memory fallback is only used when Redis is unreachable (e.g. during
    development or tests) and is not suitable for multi-instance deployments.
    """

    def __init__(self, prefix: str, limit: int, window_seconds: int) -> None:
        self.prefix = prefix
        self.limit = limit
        self.window_seconds = window_seconds

    def _key(self, identifier: str, window_start: int) -> str:
        return f"ratelimit:{self.prefix}:{identifier}:{window_start}"

    async def check(self, identifier: str) -> RateLimitResult:
        client = get_redis_client()
        try:
            return await self._check_redis(client, identifier)
        except Exception:
            return self._check_memory(identifier)

    async def _check_redis(self, client: Redis, identifier: str) -> RateLimitResult:
        now = int(time.time())
        window_start = now - (now % self.window_seconds)
        key = self._key(identifier, window_start)
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, self.window_seconds + 1)
        remaining = max(0, self.limit - count)
        if count > self.limit:
            return RateLimitResult(False, self.window_seconds, self.limit, 0)
        return RateLimitResult(True, 0, self.limit, remaining)

    def _check_memory(self, identifier: str) -> RateLimitResult:
        now = time.monotonic()
        window_start = now - (now % self.window_seconds)
        key = f"{self.prefix}:{identifier}"
        kept = [ts for ts in _memory[key] if ts >= window_start]
        if len(kept) < self.limit:
            kept.append(now)
            _memory[key] = kept
            return RateLimitResult(True, 0, self.limit, self.limit - len(kept))
        _memory[key] = kept
        return RateLimitResult(False, self.window_seconds, self.limit, 0)


def rate_limit_dependency(
    prefix: str, limit: int, window_seconds: int
) -> type[Request] | object:
    """Build a FastAPI dependency enforcing a per-IP rate limit."""

    limiter = RateLimiter(prefix, limit, window_seconds)

    async def dependency(request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return
        identifier = request.client.host if request.client else "unknown"
        result = await limiter.check(identifier)
        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(result.retry_after)},
            )

    return dependency
