"""Fail in-flight jobs when the owning user has been soft-deleted."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Job, User
from app.services.credit_metering import failure_payload


def abort_job_if_user_soft_deleted(session: Session, job: Job) -> bool:
    """If `job.user_id` points at a soft-deleted user, set job to failed and commit.

    Returns True when the job was aborted (caller should skip further work).
    """
    if not job.user_id:
        return False
    user = session.get(User, job.user_id)
    if user is None or user.deleted_at is None:
        return False
    job.payload = failure_payload("ACCOUNT_DELETED")
    job.status = "failed"
    session.commit()
    return True
