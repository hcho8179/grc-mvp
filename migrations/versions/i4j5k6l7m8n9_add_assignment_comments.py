"""Add question assignment and comments

Revision ID: i4j5k6l7m8n9
Revises: h3i4j5k6l7m8
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa

revision = 'i4j5k6l7m8n9'
down_revision = 'h3i4j5k6l7m8'
branch_labels = None
depends_on = None


def upgrade():
    # Add assigned_to_id to questions
    op.add_column('questions',
        sa.Column('assigned_to_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True)
    )
    op.create_index('ix_questions_assigned_to_id', 'questions', ['assigned_to_id'])

    # Create question_comments table
    op.create_table(
        'question_comments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('question_id', sa.Integer(),
                  sa.ForeignKey('questions.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('questionnaire_id', sa.Integer(),
                  sa.ForeignKey('questionnaires.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('org_id', sa.Integer(),
                  sa.ForeignKey('organizations.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('user_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('user_email', sa.String(256), nullable=True),
        sa.Column('user_name', sa.String(256), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
    )


def downgrade():
    op.drop_table('question_comments')
    op.drop_index('ix_questions_assigned_to_id', table_name='questions')
    op.drop_column('questions', 'assigned_to_id')
