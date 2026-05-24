"""add is_stale to approved_answers

Revision ID: a2b3c4d5e6f7
Revises: z1a2b3c4d5e6
Create Date: 2026-05-24
"""
import sqlalchemy as sa
from alembic import op

revision = 'a2b3c4d5e6f7'
down_revision = 'z1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('approved_answers', sa.Column('is_stale', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('approved_answers', 'is_stale')
