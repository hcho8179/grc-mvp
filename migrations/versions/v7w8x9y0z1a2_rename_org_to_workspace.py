"""rename organisations to workspaces

Revision ID: v7w8x9y0z1a2
Revises: u6v7w8x9y0z1
Create Date: 2026-05-23
"""
from alembic import op
import sqlalchemy as sa

revision = 'v7w8x9y0z1a2'
down_revision = 'u6v7w8x9y0z1'
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _create_answer_versions_if_missing() -> None:
    if _table_exists('answer_versions'):
        return

    op.create_table(
        'answer_versions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column(
            'question_id',
            sa.Integer(),
            sa.ForeignKey('questions.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'org_id',
            sa.Integer(),
            sa.ForeignKey('organizations.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_email', sa.String(256), nullable=True),
        sa.Column('user_name', sa.String(256), nullable=True),
        sa.Column('action', sa.String(32), nullable=False),
        sa.Column('draft_answer', sa.Text(), nullable=True),
        sa.Column('short_answer', sa.String(32), nullable=True),
    )


def _create_notifications_if_missing() -> None:
    if _table_exists('notifications'):
        return

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column(
            'org_id',
            sa.Integer(),
            sa.ForeignKey('organizations.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column('type', sa.String(64), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('resource_type', sa.String(64), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
    )


def upgrade() -> None:
    _create_answer_versions_if_missing()
    _create_notifications_if_missing()

    # Rename the primary tenant table
    op.rename_table('organizations', 'workspaces')

    # Rename org_id -> workspace_id in every table that holds the FK
    tables = [
        'users',
        'documents',
        'chunk_feedback',
        'questionnaire_templates',
        'questionnaires',
        'llm_calls',
        'approved_answers',
        'audit_logs',
        'question_comments',
        'answer_versions',
        'notifications',
        'invites',
    ]
    for table in tables:
        op.alter_column(table, 'org_id', new_column_name='workspace_id')


def downgrade() -> None:
    tables = [
        'users',
        'documents',
        'chunk_feedback',
        'questionnaire_templates',
        'questionnaires',
        'llm_calls',
        'approved_answers',
        'audit_logs',
        'question_comments',
        'answer_versions',
        'notifications',
        'invites',
    ]
    for table in tables:
        op.alter_column(table, 'workspace_id', new_column_name='org_id')

    op.rename_table('workspaces', 'organizations')
