"""add share_token to questionnaires and conflict_warning to questions

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = 'b3c4d5e6f7a8'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('questionnaires', sa.Column('share_token', sa.String(64), nullable=True))
    op.create_index('ix_questionnaires_share_token', 'questionnaires', ['share_token'], unique=True)
    op.add_column('questions', sa.Column('conflict_warning', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('questions', 'conflict_warning')
    op.drop_index('ix_questionnaires_share_token', table_name='questionnaires')
    op.drop_column('questionnaires', 'share_token')
