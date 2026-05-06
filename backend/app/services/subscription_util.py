"""Paid-plan detection — Stripe Price IDs (env) + legacy slug basic/pro."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.config import get_settings
from app.db.models import Subscription

if TYPE_CHECKING:
    from app.config import Settings


def parse_paid_price_ids(raw: str) -> frozenset[str]:
    parts = [p.strip() for p in (raw or "").split(",") if p.strip()]
    return frozenset(parts)


def infer_plan_slug(price_id: str | None, settings: "Settings") -> str:
    """Map Stripe Price → plan slug (schema chk: free | basic | pro)."""
    if not price_id:
        return "free"
    if settings.stripe_price_basic and price_id == settings.stripe_price_basic:
        return "basic"
    if settings.stripe_price_pro and price_id == settings.stripe_price_pro:
        return "pro"
    paid = parse_paid_price_ids(settings.stripe_paid_price_ids)
    if price_id in paid:
        return "pro"
    return "free"


def subscription_counts_as_paid_row(sub: Subscription) -> bool:
    settings = get_settings()
    if sub.status not in ("active", "trialing"):
        return False
    paid_ids = parse_paid_price_ids(settings.stripe_paid_price_ids)
    if sub.stripe_price_id:
        if paid_ids:
            return sub.stripe_price_id in paid_ids
        return False
    return sub.plan in ("basic", "pro")


def paid_subscription_filter_clause() -> ColumnElement[bool]:
    """Điều kiện SQL: subscription đang hiệu lực và được tính là paid."""
    settings = get_settings()
    paid_ids = parse_paid_price_ids(settings.stripe_paid_price_ids)
    active = Subscription.status.in_(("active", "trialing"))
    legacy = and_(Subscription.stripe_price_id.is_(None), Subscription.plan.in_(("basic", "pro")))
    if paid_ids:
        return active & or_(Subscription.stripe_price_id.in_(paid_ids), legacy)
    return active & legacy


def select_user_ids_with_paid_subscription() -> Select[tuple[uuid.UUID]]:
    return select(Subscription.user_id).where(paid_subscription_filter_clause()).distinct()


def user_has_paid_plan(db: Session, user_id: uuid.UUID) -> bool:
    row = db.execute(
        select(Subscription.id)
        .where(
            Subscription.user_id == user_id,
            paid_subscription_filter_clause(),
        )
        .limit(1)
    ).first()
    return row is not None


# Back-compat tests / imports — không dùng trong logic mới
_PAID_PLANS = frozenset({"basic", "pro"})
