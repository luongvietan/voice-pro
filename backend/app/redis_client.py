"""Shared async Redis client for middleware / rate limiting."""

from __future__ import annotations

import asyncio
import logging

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
_client: aioredis.Redis | None = None
_loop_id: int | None = None


async def _close_quietly(client: aioredis.Redis | None) -> None:
    if client is None:
        return
    try:
        await client.aclose()
    except Exception:
        pass


async def get_redis() -> aioredis.Redis | None:
    """Return a shared async Redis client, or None if Redis is unavailable."""
    global _client, _loop_id

    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        return None

    cur_id = id(current_loop)

    # Starlette TestClient / pytest có thể đổi hoặc đóng loop giữa các request — client
    # redis.asyncio gắn với loop cũ sẽ gây RuntimeError: Event loop is closed.
    if _client is not None and _loop_id is not None and _loop_id != cur_id:
        await _close_quietly(_client)
        _client = None
        _loop_id = None

    if _client is not None:
        try:
            await _client.ping()
            return _client
        except (aioredis.RedisError, RuntimeError, OSError):
            logger.warning("Redis connection stale, reconnecting...")
            await _close_quietly(_client)
            _client = None
            _loop_id = None

    try:
        client = aioredis.Redis.from_url(get_settings().redis_url, decode_responses=True)
        await client.ping()
        _client = client
        _loop_id = cur_id
    except aioredis.RedisError as exc:
        logger.warning("Redis unavailable for rate limiting: %s", exc)
        _client = None
        _loop_id = None
    return _client


def reset_redis_client_for_tests() -> None:
    """Đồng bộ reset singleton (pytest); tránh giữ connection gắn loop đã đóng."""
    global _client, _loop_id
    _client = None
    _loop_id = None
