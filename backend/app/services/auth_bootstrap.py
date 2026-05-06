from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import Credits, RefreshToken, User
from app.security.tokens import create_access_token, hash_refresh_token, new_refresh_token_value
from app.services.subscription_util import user_has_paid_plan


def ensure_credits_row(db: Session, user: User, settings: Settings) -> Credits:
    if user.credits_row is not None:
        return user.credits_row
    row = Credits(user_id=user.id, balance_minutes=settings.initial_free_minutes)
    db.add(row)
    db.flush()
    return row


def persist_refresh_token(db: Session, user_id: uuid.UUID, settings: Settings) -> str:
    raw = new_refresh_token_value()
    expires = datetime.now(tz=UTC) + timedelta(days=settings.jwt_refresh_expire_days)
    row = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw),
        expires_at=expires,
    )
    db.add(row)
    return raw


def build_token_response(
    db: Session,
    user: User,
    settings: Settings,
) -> tuple[str, str, dict]:
    credits = ensure_credits_row(db, user, settings)
    access = create_access_token(user.id, settings)
    refresh_raw = persist_refresh_token(db, user.id, settings)
    is_paid = user_has_paid_plan(db, user.id)
    user_payload = {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "balance_minutes": credits.balance_minutes,
        "is_paid": is_paid,
    }
    return access, refresh_raw, user_payload


def revoke_refresh_by_raw(db: Session, raw: str | None) -> None:
    if not raw:
        return
    h = hash_refresh_token(raw)
    row = db.query(RefreshToken).filter(RefreshToken.token_hash == h).one_or_none()
    if row:
        db.delete(row)
