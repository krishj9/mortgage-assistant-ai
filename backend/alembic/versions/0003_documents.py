"""Add documents and document_extractions tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_documents"
down_revision = "0002_chat_turns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("deal_id", sa.Integer(), sa.ForeignKey("deals.id"), nullable=False),
        sa.Column("storage_uri", sa.String(length=1024), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False, server_default="application/pdf"),
        sa.Column("predicted_type", sa.String(length=64), nullable=False, server_default="unknown"),
        sa.Column("classification_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("extraction_status", sa.String(length=64), nullable=False, server_default="pending"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_documents_deal_id", "documents", ["deal_id"], unique=False)

    op.create_table(
        "document_extractions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=False, unique=True),
        sa.Column("raw_ocr", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("normalized", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("confidence", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("human_corrections", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_document_extractions_document_id", "document_extractions", ["document_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_document_extractions_document_id", table_name="document_extractions")
    op.drop_table("document_extractions")
    op.drop_index("ix_documents_deal_id", table_name="documents")
    op.drop_table("documents")
