"""Initial Phase-1 schema: users, borrowers, deals, loan applications, deal context, messages."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.models.deal import DealStatus

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users (staff)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Borrowers
    op.create_table(
        "borrowers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "dob_placeholder",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'0000-00-00'"),
        ),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("contact_phone", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_borrowers_contact_email", "borrowers", ["contact_email"], unique=True)

    # Deals
    op.create_table(
        "deals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("borrower_id", sa.Integer(), sa.ForeignKey("borrowers.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum(*[s.value for s in DealStatus], name="deal_status"),
            nullable=False,
            server_default=sa.text(f"'{DealStatus.intake_in_progress.value}'"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_deals_borrower_id", "deals", ["borrower_id"])

    # Loan Application
    op.create_table(
        "loan_applications",
        sa.Column(
            "deal_id",
            sa.Integer(),
            sa.ForeignKey("deals.id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("data", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Deal context
    op.create_table(
        "deal_contexts",
        sa.Column(
            "deal_id",
            sa.Integer(),
            sa.ForeignKey("deals.id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("extracted_income", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("extracted_assets", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("extracted_liabilities", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("computed_metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("status_flags", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Messages
    op.create_table(
        "messages",
        sa.Column(
            "deal_id",
            sa.Integer(),
            sa.ForeignKey("deals.id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("internal_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("borrower_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("internal_approved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("borrower_approved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("deal_contexts")
    op.drop_table("loan_applications")
    op.drop_table("deals")
    op.drop_table("borrowers")
    op.drop_table("users")

