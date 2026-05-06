from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.config import Settings


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def new_refresh_token_value() -> str:
    return secrets.token_urlsafe(48)


def create_access_token(user_id: uuid.UUID, settings: Settings) -> str:
    expire = datetime.now(tz=UTC) + timedelta(minutes=settings.jwt_access_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire, "typ": "access"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def decode_access_token(token: str, settings: Settings) -> uuid.UUID:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    if payload.get("typ") != "access":
        raise jwt.InvalidTokenError("not an access token")
    sub = payload.get("sub")
    if not sub:
        raise jwt.InvalidTokenError("missing sub")
    return uuid.UUID(str(sub))


def try_decode_access_user_id(token: str, settings: Settings) -> uuid.UUID | None:
    """Best-effort for rate-limit buckets; returns None if token invalid."""
    try:
        return decode_access_token(token, settings)
    except (jwt.PyJWTError, ValueError):
        return None
