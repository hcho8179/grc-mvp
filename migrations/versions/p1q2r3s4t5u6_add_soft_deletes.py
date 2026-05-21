"""Add deleted_at to questionnaires and documents for soft delete.

Revision ID: p1q2r3s4t5u6
Revises: o0p1q2r3s4t5
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa

revision = 'p1q2r3s4t5u6'
down_revision = 'o0p1q2r3s4t5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('questionnaires',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_questionnaires_deleted_at', 'questionnaires', ['deleted_at'])

    op.add_column('documents',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_documents_deleted_at', 'documents', ['deleted_at'])


def downgrade():
    op.drop_index('ix_documents_deleted_at', table_name='documents')
    op.drop_column('documents', 'deleted_at')
    op.drop_index('ix_questionnaires_deleted_at', table_name='questionnaires')
    op.drop_column('questionnaires', 'deleted_at')
