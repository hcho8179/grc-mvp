"""Add raw_xlsx_key to questionnaires for S3 storage.

Revision ID: n9o0p1q2r3s4
Revises: m8n9o0p1q2r3
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa

revision = 'n9o0p1q2r3s4'
down_revision = 'm8n9o0p1q2r3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('questionnaires',
        sa.Column('raw_xlsx_key', sa.String(512), nullable=True))


def downgrade():
    op.drop_column('questionnaires', 'raw_xlsx_key')
