"""restore is_firm and firm_workspace_id on workspaces

Revision ID: y0z1a2b3c4d5
Revises: x9y0z1a2b3c4
Create Date: 2026-05-24
"""
import sqlalchemy as sa
from alembic import op

revision = 'y0z1a2b3c4d5'
down_revision = 'x9y0z1a2b3c4'
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
