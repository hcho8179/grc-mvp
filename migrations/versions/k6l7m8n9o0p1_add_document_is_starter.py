"""Add is_starter flag to documents

Revision ID: k6l7m8n9o0p1
Revises: j5k6l7m8n9o0
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa

revision = 'k6l7m8n9o0p1'
down_revision = 'j5k6l7m8n9o0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('documents',
        sa.Column('is_starter', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade():
    op.drop_column('documents', 'is_starter')
