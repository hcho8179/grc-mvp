"""add white_label_export, share_token, conflict_warning

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = 'd5e6f7a8b9c0'
down_revision = 'c4d5e6f7a8b9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('workspaces', sa.Column('white_label_export', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('questionnaires', sa.Column('share_token', sa.String(64), nullable=True))
    op.create_index('ix_questionnaires_share_token', 'questionnaires', ['share_token'], unique=True)
    op.add_column('questions', sa.Column('conflict_warning', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('questions', 'conflict_warning')
    op.drop_index('ix_questionnaires_share_token', table_name='questionnaires')
    op.drop_column('questionnaires', 'share_token')
    op.drop_column('workspaces', 'white_label_export')
