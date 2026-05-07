"""Epic 7 — explicit ON DELETE for user-owned rows (hard delete safety + no silent orphans)."""

from collections.abc import Sequence

from alembic import op

revision: str = "006_epic7_fk_on_delete"
down_revision: str | None = "005_epic7_soft_delete"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("fk_jobs_user_id_users", "jobs", type_="foreignkey")
    op.create_foreign_key(
        "fk_jobs_user_id_users",
        "jobs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_constraint("fk_credits_user_id_users", "credits", type_="foreignkey")
    op.create_foreign_key(
        "fk_credits_user_id_users",
        "credits",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_credit_transactions_user_id_users", "credit_transactions", type_="foreignkey")
    op.create_foreign_key(
        "fk_credit_transactions_user_id_users",
        "credit_transactions",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_refresh_tokens_user_id_users", "refresh_tokens", type_="foreignkey")
    op.create_foreign_key(
        "fk_refresh_tokens_user_id_users",
        "refresh_tokens",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_subscriptions_user_id_users", "subscriptions", type_="foreignkey")
    op.create_foreign_key(
        "fk_subscriptions_user_id_users",
        "subscriptions",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_subscriptions_user_id_users", "subscriptions", type_="foreignkey")
    op.create_foreign_key(
        "fk_subscriptions_user_id_users",
        "subscriptions",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_constraint("fk_refresh_tokens_user_id_users", "refresh_tokens", type_="foreignkey")
    op.create_foreign_key(
        "fk_refresh_tokens_user_id_users",
        "refresh_tokens",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_constraint("fk_credit_transactions_user_id_users", "credit_transactions", type_="foreignkey")
    op.create_foreign_key(
        "fk_credit_transactions_user_id_users",
        "credit_transactions",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_constraint("fk_credits_user_id_users", "credits", type_="foreignkey")
    op.create_foreign_key(
        "fk_credits_user_id_users",
        "credits",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_constraint("fk_jobs_user_id_users", "jobs", type_="foreignkey")
    op.create_foreign_key(
        "fk_jobs_user_id_users",
        "jobs",
        "users",
        ["user_id"],
        ["id"],
    )
