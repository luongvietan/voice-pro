"""Soft-delete user account: revoke sessions, clear PII-bearing columns."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import stripe
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import RefreshToken, Subscription, User

logger = logging.getLogger(__name__)

_CANCELLABLE_STATUSES = {"active", "trialing", "past_due"}


def _cancel_stripe_subscriptions(db: Session, user: User) -> None:
    """Best-effort: cancel active Stripe subscriptions on Stripe before soft-delete."""
    settings = get_settings()
    if not settings.stripe_api_key:
        return
    subs = db.scalars(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.stripe_subscription_id.isnot(None),
            Subscription.status.in_(_CANCELLABLE_STATUSES),
        )
    ).all()
    if not subs:
        return
    stripe.api_key = settings.stripe_api_key
    for sub in subs:
        try:
            stripe.Subscription.cancel(sub.stripe_subscription_id)
        except Exception:
            logger.warning(
                "Failed to cancel Stripe subscription %s for user %s — continuing soft-delete",
                sub.stripe_subscription_id,
                user.id,
            )


def soft_delete_user(db: Session, user: User) -> None:
    """Mark user deleted, remove refresh tokens, clear fields used for login / PII.

    Cancels active Stripe subscriptions (best-effort) before clearing stripe_customer_id.
    """
    _cancel_stripe_subscriptions(db, user)
    now = datetime.now(tz=UTC)
    user.deleted_at = now
    user.email = None
    user.google_sub = None
    user.password_hash = None
    user.display_name = None
    user.avatar_url = None
    user.settings_json = {}
    user.stripe_customer_id = None
    db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    db.flush()
