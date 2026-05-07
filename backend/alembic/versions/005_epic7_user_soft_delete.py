"""Epic 7 — soft delete account (deleted_at on users)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_epic7_soft_delete"
down_revision: str | None = "004_epic6_stripe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_users_deleted_at", table_name="users")
    op.drop_column("users", "deleted_at")
