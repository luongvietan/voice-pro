"""Periodic free-tier credit reset (Epic 4)."""

from __future__ import annotations

import logging

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import get_settings
from app.db.models import Credits
from app.db.session import get_session_factory
from app.services.subscription_util import select_user_ids_with_paid_subscription

logger = logging.getLogger(__name__)


@celery_app.task(name="credits.reset_free_tier_monthly")
def reset_free_tier_monthly() -> dict[str, int]:
    """Ngày 1 mỗi tháng UTC: user free tier nhận lại INITIAL_FREE_MINUTES."""
    settings = get_settings()
    factory = get_session_factory()
    session: Session = factory()
    try:
        paid_sq = select_user_ids_with_paid_subscription().subquery()
        result = session.execute(
            update(Credits)
            .where(Credits.user_id.not_in(select(paid_sq.c.user_id)))
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
