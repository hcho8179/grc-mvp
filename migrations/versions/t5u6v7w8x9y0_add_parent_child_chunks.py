"""add parent_chunk_id and is_leaf to knowledge_chunks for hierarchical retrieval

Revision ID: t5u6v7w8x9y0
Revises: s4t5u6v7w8x9
Create Date: 2026-05-23
"""
from alembic import op
import sqlalchemy as sa

revision = 't5u6v7w8x9y0'
down_revision = 's4t5u6v7w8x9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("knowledge_chunks",
        sa.Column("is_leaf", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("knowledge_chunks",
        sa.Column("parent_chunk_id", sa.Integer(),
                  sa.ForeignKey("knowledge_chunks.id", ondelete="CASCADE"),
                  nullable=True))
    op.create_index("ix_knowledge_chunks_parent_chunk_id",
                    "knowledge_chunks", ["parent_chunk_id"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_chunks_parent_chunk_id", "knowledge_chunks")
    op.drop_column("knowledge_chunks", "parent_chunk_id")
    op.drop_column("knowledge_chunks", "is_leaf")
