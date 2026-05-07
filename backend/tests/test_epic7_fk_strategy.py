"""Epic 7 — FK ON DELETE strategy + soft-delete job guard."""

from __future__ import annotations

import uuid

from sqlalchemy import text

from app.db.models import Job, User
from app.db.session import get_engine, get_session_factory
from app.services.account_deletion import soft_delete_user
from app.services.job_account_guard import abort_job_if_user_soft_deleted


def test_information_schema_user_fk_delete_rules(postgres_live):
    expected = {
        "fk_jobs_user_id_users": "SET NULL",
        "fk_credits_user_id_users": "CASCADE",
        "fk_credit_transactions_user_id_users": "CASCADE",
        "fk_refresh_tokens_user_id_users": "CASCADE",
        "fk_subscriptions_user_id_users": "CASCADE",
    }
    eng = get_engine()
    with eng.connect() as conn:
        for cname, rule in expected.items():
            q = text(
                "SELECT delete_rule FROM information_schema.referential_constraints "
                "WHERE constraint_schema = 'public' AND constraint_name = :cname"
            )
            got = conn.execute(q, {"cname": cname}).scalar_one()
            assert got == rule, (cname, got)


def test_abort_job_when_owner_soft_deleted(postgres_live):
    factory = get_session_factory()
    s = factory()
    email = f"fk{uuid.uuid4().hex[:10]}@example.com"
    u = User(email=email, settings_json={})
    s.add(u)
    s.flush()
    j = Job(user_id=u.id, status="pending")
    s.add(j)
    s.commit()
    jid = j.id

    soft_delete_user(s, u)
    s.commit()
    s.close()

    s2 = factory()
    job = s2.get(Job, jid)
    assert job is not None
    assert abort_job_if_user_soft_deleted(s2, job) is True
    s2.refresh(job)
    assert job.status == "failed"
    assert "ACCOUNT_DELETED" in (job.payload or "")
    s2.close()
