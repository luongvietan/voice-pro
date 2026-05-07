"""Redis-backed rate limiting (Epic 4 — abuse prevention)."""

from __future__ import annotations

import logging
import time
from typing import Callable

import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings
from app.redis_client import get_redis
from app.security.tokens import try_decode_access_user_id

logger = logging.getLogger(__name__)

_FAIL_OPEN_LOG_INTERVAL_SEC = 60.0
_last_fail_open_log_mono: float | None = None


def reset_rate_limit_fail_open_log_throttle_for_tests() -> None:
    """pytest: reset throttle giữa các test."""
    global _last_fail_open_log_mono
    _last_fail_open_log_mono = None


def _log_redis_fail_open_throttled(reason: str) -> None:
    """ERROR có prefix cố định; tối đa 1 log / 60s mỗi process (Epic 9.3)."""
    global _last_fail_open_log_mono
    now = time.monotonic()
    if _last_fail_open_log_mono is not None and (now - _last_fail_open_log_mono) < _FAIL_OPEN_LOG_INTERVAL_SEC:
        return
    _last_fail_open_log_mono = now
    logger.error("[rate_limit] redis_unavailable_fail_open %s", reason)


def _client_ip(request: Request) -> str | None:
    """Return the real client IP, or None if undeterminable.

    P2: X-Forwarded-For is NOT trusted — it is trivially spoofable by any
    client. Only the TCP-level peer address (request.client.host) is used.
    Production deployments behind a trusted reverse proxy should configure
    the proxy to overwrite X-Real-IP and read that instead.
    """
    if request.client:
        return request.client.host
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP (+ optional user id) counters:
    - >100 requests / hour → 429
    - burst >20 / 10s → 1h block
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if path == "/health" or path in ("/openapi.json", "/redoc", "/favicon.ico") or path.startswith(
            ("/docs", "/static/")
        ):
            return await call_next(request)

        # P3: use async Redis client to avoid blocking the event loop
        r = await get_redis()
        if r is None:
            _log_redis_fail_open_throttled("get_redis_returned_none")
            return await call_next(request)

        # P13: if client IP is unknown, skip rate limiting rather than sharing a
        # single "unknown" bucket that one client could exhaust for everyone
        ip = _client_ip(request)
        if ip is None:
            return await call_next(request)

        settings = get_settings()
        auth = request.headers.get("authorization") or ""
        bucket = ip
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
            uid = try_decode_access_user_id(token, settings)
            if uid is not None:
                bucket = f"{ip}:u:{uid}"

        try:
            block_key = f"vp:rl:block:{bucket}"
            if await r.exists(block_key):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests — temporarily blocked."},
                    headers={"Retry-After": "3600"},
                )

            # P4: use pipeline so INCR + EXPIRE are sent atomically in one round-trip;
            # eliminates the "key created with no TTL" race if the process crashes
            # between the two commands
            burst_key = f"vp:rl:burst:{bucket}"
            async with r.pipeline(transaction=False) as pipe:
                pipe.incr(burst_key)
                pipe.expire(burst_key, 10)
                burst, _ = await pipe.execute()

            if burst > 20:
                await r.setex(block_key, 3600, "1")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Burst limit exceeded — try again later."},
                    headers={"Retry-After": "3600"},
                )

            hour_key = f"vp:rl:hour:{bucket}"
            async with r.pipeline(transaction=False) as pipe:
                pipe.incr(hour_key)
                pipe.expire(hour_key, 3600)
                hour_n, _ = await pipe.execute()

            if hour_n > 100:
                ttl = await r.ttl(hour_key)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Hourly rate limit exceeded."},
                    headers={"Retry-After": str(ttl or 3600)},
                )

        except aioredis.RedisError:
            # P15: Redis error mid-dispatch — fail open so the API stays available
            _log_redis_fail_open_throttled("redis_error_mid_dispatch")
            return await call_next(request)

        return await call_next(request)
