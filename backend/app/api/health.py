import asyncio
from typing import Literal

import redis.asyncio as redis_async
from fastapi import APIRouter
from sqlalchemy import text

from app.config import get_settings
from app.db.session import get_engine

router = APIRouter()

_DB_TIMEOUT_SECONDS = 3.0
_REDIS_TIMEOUT_SECONDS = 3.0


def _check_db_sync() -> bool:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _check_redis() -> bool:
    settings = get_settings()
    client = redis_async.from_url(settings.redis_url, encoding="utf-8", decode_responses=True, socket_connect_timeout=_REDIS_TIMEOUT_SECONDS, socket_timeout=_REDIS_TIMEOUT_SECONDS)
    try:
        await client.ping()
        return True
    except Exception:
        return False
    finally:
        await client.aclose()


@router.get("/health")
async def health() -> dict[str, Literal["ok", "degraded"] | Literal["connected", "disconnected"]]:
    db_task = asyncio.to_thread(_check_db_sync)
    redis_task = _check_redis()
    db_ok, redis_ok = await asyncio.gather(
        asyncio.wait_for(db_task, timeout=_DB_TIMEOUT_SECONDS),
        asyncio.wait_for(redis_task, timeout=_REDIS_TIMEOUT_SECONDS),
        return_exceptions=True,
    )
    db_ok = db_ok is True
    redis_ok = redis_ok is True

    status: Literal["ok", "degraded"] = "ok" if db_ok and redis_ok else "degraded"
    return {
        "status": status,
        "db": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
    }
