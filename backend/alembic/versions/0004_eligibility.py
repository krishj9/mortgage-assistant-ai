"""Add eligibility/conditions on deal_context and message draft/approval columns."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004_eligibility"
down_revision = "0003_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deal_contexts",
        sa.Column("eligibility", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    op.add_column(
        "deal_contexts",
        sa.Column("conditions", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )

    op.add_column(
        "messages",
        sa.Column("internal_draft", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "messages",
        sa.Column("borrower_draft", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column("messages", sa.Column("approved_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("messages", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE messages SET internal_draft = internal_notes WHERE internal_draft = ''")
    op.execute("UPDATE messages SET borrower_draft = borrower_message WHERE borrower_draft = ''")


def downgrade() -> None:
    op.drop_column("messages", "approved_at")
    op.drop_column("messages", "approved_by_user_id")
    op.drop_column("messages", "borrower_draft")
    op.drop_column("messages", "internal_draft")
    op.drop_column("deal_contexts", "conditions")
    op.drop_column("deal_contexts", "eligibility")
