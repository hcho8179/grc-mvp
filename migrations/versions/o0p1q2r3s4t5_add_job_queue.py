"""Add job_queue table for persistent background task processing.

Revision ID: o0p1q2r3s4t5
Revises: n9o0p1q2r3s4
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa

revision = 'o0p1q2r3s4t5'
down_revision = 'n9o0p1q2r3s4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'job_queue',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('job_type', sa.String(64), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(16), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('run_after', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_job_queue_status', 'job_queue', ['status'])
    op.create_index('ix_job_queue_created_at', 'job_queue', ['created_at'])


def downgrade():
    op.drop_index('ix_job_queue_created_at', table_name='job_queue')
    op.drop_index('ix_job_queue_status', table_name='job_queue')
    op.drop_table('job_queue')
