"""Add event_logs audit table."""

from alembic import op
import sqlalchemy as sa


revision = "0006_event_logs"
down_revision = "0005_chat_turn_role_varchar"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("deal_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("payload_snapshot", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_logs_deal_id", "event_logs", ["deal_id"])
    op.create_index("ix_event_logs_kind", "event_logs", ["kind"])


def downgrade() -> None:
    op.drop_index("ix_event_logs_kind", table_name="event_logs")
    op.drop_index("ix_event_logs_deal_id", table_name="event_logs")
    op.drop_table("event_logs")
