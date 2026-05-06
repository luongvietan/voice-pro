"""Deduct free-tier minutes when a transcribe job completes (Epic 4)."""

from __future__ import annotations

import json
import math
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import CreditTransaction, Credits, Job
from app.services.subscription_util import user_has_paid_plan


def minutes_to_charge(duration_seconds: float) -> int:
    """Billable minutes: ceil(audio_seconds / 60), zero if no duration."""
    if duration_seconds <= 0:
        return 0
    # P11: guard against inf/nan which would cause OverflowError in math.ceil
    if not math.isfinite(duration_seconds):
        return 0
    return max(1, math.ceil(duration_seconds / 60.0))


def apply_transcribe_credit_metering(
    session: Session,
    *,
    job: Job,
    duration_seconds: float,
) -> tuple[bool, str | None]:
    """
    On successful STT: for free-tier users, deduct minutes and log credit_transactions.
    Paid users: no-op.
    Returns (success, error_code) — on failure job should be marked failed by caller.
    """
    if job.user_id is None:
        return True, None

    if user_has_paid_plan(session, job.user_id):
        return True, None

    minutes = minutes_to_charge(duration_seconds)
    if minutes == 0:
        return True, None

    existing = session.execute(
        select(CreditTransaction.id).where(CreditTransaction.job_id == job.id).limit(1)
    ).first()
    if existing is not None:
        return True, None

    credits = session.execute(
        select(Credits).where(Credits.user_id == job.user_id).with_for_update()
    ).scalar_one_or_none()
    if credits is None:
        return False, "CREDITS_ROW_MISSING"

    if credits.balance_minutes < minutes:
        return False, "CREDIT_EXHAUSTED"

    credits.balance_minutes -= minutes
    session.add(
        CreditTransaction(
            user_id=job.user_id,
            job_id=job.id,
            delta_minutes=-minutes,
            balance_after=credits.balance_minutes,
        )
    )
    try:
        session.flush()
    except IntegrityError:
        # P10: concurrent task for the same job already committed the transaction
        # (unique constraint on job_id) — treat as idempotent success
        session.rollback()
    return True, None


def failure_payload(code: str) -> str:
    return json.dumps({"error": "Insufficient credits for this audio length.", "code": code})
