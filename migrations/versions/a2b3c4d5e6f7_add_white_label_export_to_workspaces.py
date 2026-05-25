"""add white_label_export to workspaces

Revision ID: a2b3c4d5e6f7
Revises: z1a2b3c4d5e6
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = 'a2b3c4d5e6f7'
down_revision = 'z1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('workspaces', sa.Column('white_label_export', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('workspaces', 'white_label_export')
