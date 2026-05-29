"""Convert legacy chat_turns.role enum to varchar (matches ORM + 0002)."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_chat_turn_role_varchar"
down_revision = "0004_eligibility"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    row = bind.execute(
        sa.text(
            """
            SELECT udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'chat_turns'
              AND column_name = 'role'
            """
        )
    ).fetchone()
    if row is None:
        return
    if row.udt_name == "chat_role":
        op.execute(
            "ALTER TABLE chat_turns ALTER COLUMN role TYPE VARCHAR(32) USING role::text"
        )
        op.execute("DROP TYPE chat_role")


def downgrade() -> None:
    # No-op: prior enum definition is not restored.
    pass
