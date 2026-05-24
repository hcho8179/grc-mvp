"""replace assigned_to_id with flag_note on questions

Revision ID: z1a2b3c4d5e6
Revises: y0z1a2b3c4d5
Create Date: 2026-05-24
"""
import sqlalchemy as sa
from alembic import op

revision = 'z1a2b3c4d5e6'
down_revision = 'y0z1a2b3c4d5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('questions', sa.Column('flag_note', sa.Text(), nullable=True))
    op.drop_index('ix_questions_assigned_to_id', table_name='questions', if_exists=True)
    op.drop_constraint('questions_assigned_to_id_fkey', 'questions', type_='foreignkey')
    op.drop_column('questions', 'assigned_to_id')


def downgrade() -> None:
    op.add_column('questions', sa.Column('assigned_to_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'questions_assigned_to_id_fkey', 'questions', 'users',
        ['assigned_to_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index('ix_questions_assigned_to_id', 'questions', ['assigned_to_id'])
    op.drop_column('questions', 'flag_note')
