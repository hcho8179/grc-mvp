"""Add email verification fields to users table.

Revision ID: l7m8n9o0p1q2
Revises: k6l7m8n9o0p1
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa

revision = 'l7m8n9o0p1q2'
down_revision = 'k6l7m8n9o0p1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('verification_token_hash', sa.String(256), nullable=True))
    op.add_column('users', sa.Column('verification_token_expires', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_users_verification_token_hash', 'users', ['verification_token_hash'])


def downgrade():
    op.drop_index('ix_users_verification_token_hash', table_name='users')
    op.drop_column('users', 'verification_token_expires')
    op.drop_column('users', 'verification_token_hash')
    op.drop_column('users', 'email_verified')
