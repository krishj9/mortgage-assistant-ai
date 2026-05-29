"""Add chat_turns table for borrower chat intake."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_chat_turns"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_turns",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("deal_id", sa.Integer(), sa.ForeignKey("deals.id"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("structured_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_turns_deal_id", "chat_turns", ["deal_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_chat_turns_deal_id", table_name="chat_turns")
    op.drop_table("chat_turns")

