"""add chunk_feedback table for RAG relevance learning

Revision ID: s4t5u6v7w8x9
Revises: r3s4t5u6v7w8
Create Date: 2026-05-23
"""
from alembic import op
import sqlalchemy as sa

revision = 's4t5u6v7w8x9'
down_revision = 'r3s4t5u6v7w8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chunk_feedback",
        sa.Column("id",         sa.Integer(),     primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("chunk_id",   sa.Integer(),     sa.ForeignKey("knowledge_chunks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("org_id",     sa.Integer(),     sa.ForeignKey("organizations.id",    ondelete="CASCADE"), nullable=False),
        sa.Column("signal",     sa.String(8),     nullable=False),
    )
    op.create_index("ix_chunk_feedback_chunk_id", "chunk_feedback", ["chunk_id"])
    op.create_index("ix_chunk_feedback_org_id",   "chunk_feedback", ["org_id"])


def downgrade() -> None:
    op.drop_table("chunk_feedback")
