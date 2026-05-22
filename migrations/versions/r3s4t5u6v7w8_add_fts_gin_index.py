"""add GIN index on knowledge_chunks.text for full-text search

Revision ID: r3s4t5u6v7w8
Revises: q2r3s4t5u6v7
Create Date: 2026-05-23
"""
from alembic import op

revision = 'r3s4t5u6v7w8'
down_revision = 'q2r3s4t5u6v7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_knowledge_chunks_fts
        ON knowledge_chunks
        USING gin(to_tsvector('english', text))
    """)


def downgrade() -> None:
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_knowledge_chunks_fts")
