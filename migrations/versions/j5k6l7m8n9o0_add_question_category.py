"""Add category column to questions

Revision ID: j5k6l7m8n9o0
Revises: i4j5k6l7m8n9
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa

revision = 'j5k6l7m8n9o0'
down_revision = 'i4j5k6l7m8n9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('questions',
        sa.Column('category', sa.String(64), nullable=True)
    )
    op.create_index('ix_questions_category', 'questions', ['category'])


def downgrade():
    op.drop_index('ix_questions_category', table_name='questions')
    op.drop_column('questions', 'category')
