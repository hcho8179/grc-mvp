"""phase8_questionnaire_templates

Revision ID: f1c2d3e4f5a6
Revises: e7f8a9b0c1d2
Create Date: 2026-05-20

Adds:
  - questionnaire_templates table
  - questionnaires.question_col_index column
  - questionnaires.template_id FK column
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "questionnaire_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("customer_name", sa.String(256), nullable=True),
        sa.Column("question_col", sa.Integer(), nullable=False),
        sa.Column("answer_col", sa.Integer(), nullable=True),
        sa.Column("format_config", sa.JSON(), nullable=True),
        sa.Column("times_used", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_questionnaire_templates_customer_name", "questionnaire_templates", ["customer_name"])

    op.add_column("questionnaires", sa.Column("question_col_index", sa.Integer(), nullable=True))
    op.add_column(
        "questionnaires",
        sa.Column(
            "template_id",
            sa.Integer(),
            sa.ForeignKey("questionnaire_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("questionnaires", "template_id")
    op.drop_column("questionnaires", "question_col_index")
    op.drop_index("ix_questionnaire_templates_customer_name", "questionnaire_templates")
    op.drop_table("questionnaire_templates")
