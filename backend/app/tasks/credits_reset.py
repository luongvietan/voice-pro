"""Periodic free-tier credit reset (Epic 4)."""

from __future__ import annotations

import logging

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import get_settings
from app.db.models import Credits, Subscription
from app.db.session import get_session_factory
from app.services.subscription_util import _PAID_PLANS

logger = logging.getLogger(__name__)


@celery_app.task(name="credits.reset_free_tier_monthly")
def reset_free_tier_monthly() -> dict[str, int]:
    """Ngày 1 mỗi tháng UTC: user free tier nhận lại INITIAL_FREE_MINUTES."""
    settings = get_settings()
    factory = get_session_factory()
    session: Session = factory()
    try:
        # P9+P6: single bulk UPDATE instead of N+1 loop, atomic at DB level to
        # avoid lost-update race with concurrent credit deductions
        paid_user_subquery = (
            select(Subscription.user_id)
            .where(
                Subscription.status == "active",
                Subscription.plan.in_(_PAID_PLANS),
            )
            .subquery()
        )
        result = session.execute(
            update(Credits)
            .where(Credits.user_id.not_in(select(paid_user_subquery.c.user_id)))
            .values(balance_minutes=settings.initial_free_minutes)
            .execution_options(synchronize_session=False)
        )
        updated = result.rowcount
        session.commit()
        logger.info("reset_free_tier_monthly: updated=%s rows", updated)
        return {"updated": updated, "skipped_paid": 0}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
