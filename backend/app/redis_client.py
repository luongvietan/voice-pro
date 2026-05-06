"""Shared async Redis client for middleware / rate limiting."""

from __future__ import annotations

import logging

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis | None:
    """Return a shared async Redis client, or None if Redis is unavailable."""
    global _client
    if _client is not None:
        # P15: probe for stale connection — if Redis restarted, reset and reconnect
        try:
            await _client.ping()
            return _client
        except aioredis.RedisError:
            logger.warning("Redis connection stale, reconnecting...")
            _client = None

    try:
        client = aioredis.Redis.from_url(get_settings().redis_url, decode_responses=True)
        await client.ping()
        _client = client
    except aioredis.RedisError as exc:
        logger.warning("Redis unavailable for rate limiting: %s", exc)
        _client = None
    return _client
