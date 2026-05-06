"""Epic 4 — credit_transactions for metering audit trail."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_epic4_credits"
down_revision: str | None = "002_epic3_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "credit_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delta_minutes", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_credit_transactions_user_id_users"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name="fk_credit_transactions_job_id_jobs"),
        sa.UniqueConstraint("job_id", name="uq_credit_transactions_job_id"),
    )
    op.create_index("ix_credit_transactions_user_id", "credit_transactions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_credit_transactions_user_id", table_name="credit_transactions")
    op.drop_table("credit_transactions")
