"""add upload_sessions table

Revision ID: 002e6ee6d25e
Revises: 14175d109ff7
Create Date: 2026-06-03 00:35:44.128943

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002e6ee6d25e'
down_revision: Union[str, Sequence[str], None] = '14175d109ff7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'upload_sessions',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('workspace_id', sa.Integer, sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('filename', sa.String(512), nullable=False),
        sa.Column('file_type', sa.String(16), nullable=False),
        sa.Column('name', sa.String(512), nullable=False),
        sa.Column('customer_name', sa.String(256), nullable=True),
        sa.Column('file_bytes', sa.LargeBinary, nullable=False),
        sa.Column('pre_extracted_questions', sa.JSON, nullable=True),
    )


def downgrade() -> None:
    op.drop_table('upload_sessions')
