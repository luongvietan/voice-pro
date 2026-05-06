"""Paid-plan detection (Epic 4 metering skip — Epic 6 fills Stripe details)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Subscription

_PAID_PLANS = frozenset({"basic", "pro"})


def user_has_paid_plan(db: Session, user_id: uuid.UUID) -> bool:
    row = db.execute(
        select(Subscription.id).where(
            Subscription.user_id == user_id,
            Subscription.status == "active",
            Subscription.plan.in_(_PAID_PLANS),
        ).limit(1)
    ).first()
    return row is not None
