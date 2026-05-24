"""rename organisations to workspaces

Revision ID: v7w8x9y0z1a2
Revises: u6v7w8x9y0z1
Create Date: 2026-05-23
"""
from alembic import op

revision = 'v7w8x9y0z1a2'
down_revision = 'u6v7w8x9y0z1'
branch_labels = None
depends_on = None


def upgrade() -> None:
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
