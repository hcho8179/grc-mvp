"""add firm workspace support

Revision ID: w8x9y0z1a2b3
Revises: v7w8x9y0z1a2
Create Date: 2026-05-23
"""
from alembic import op
import sqlalchemy as sa

revision = 'w8x9y0z1a2b3'
down_revision = 'v7w8x9y0z1a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('workspaces', sa.Column('is_firm', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('workspaces', sa.Column('firm_workspace_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_workspaces_firm_workspace_id',
        'workspaces', 'workspaces',
        ['firm_workspace_id'], ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_workspaces_firm_workspace_id', 'workspaces', ['firm_workspace_id'])


def downgrade() -> None:
    op.drop_index('ix_workspaces_firm_workspace_id', table_name='workspaces')
    op.drop_constraint('fk_workspaces_firm_workspace_id', 'workspaces', type_='foreignkey')
    op.drop_column('workspaces', 'firm_workspace_id')
    op.drop_column('workspaces', 'is_firm')
