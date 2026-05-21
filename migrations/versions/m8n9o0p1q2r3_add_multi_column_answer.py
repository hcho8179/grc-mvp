"""Add secondary_answer_col_index to questionnaires and short_answer to questions.

Revision ID: m8n9o0p1q2r3
Revises: l7m8n9o0p1q2
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa

revision = 'm8n9o0p1q2r3'
down_revision = 'l7m8n9o0p1q2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('questionnaires',
        sa.Column('secondary_answer_col_index', sa.Integer(), nullable=True))
    op.add_column('questions',
        sa.Column('short_answer', sa.String(32), nullable=True))


def downgrade():
    op.drop_column('questions', 'short_answer')
    op.drop_column('questionnaires', 'secondary_answer_col_index')
