"""add customer_name to approved_answers and knowledge_chunks

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-05-24
"""
import sqlalchemy as sa
from alembic import op

revision = 'c4d5e6f7a8b9'
down_revision = 'b3c4d5e6f7a8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('approved_answers', sa.Column('customer_name', sa.String(256), nullable=True))
    op.create_index('ix_approved_answers_customer_name', 'approved_answers', ['customer_name'])
    op.add_column('knowledge_chunks', sa.Column('customer_name', sa.String(256), nullable=True))


def downgrade() -> None:
    op.drop_index('ix_approved_answers_customer_name', table_name='approved_answers')
    op.drop_column('approved_answers', 'customer_name')
    op.drop_column('knowledge_chunks', 'customer_name')
