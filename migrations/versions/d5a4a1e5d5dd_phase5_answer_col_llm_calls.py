"""phase5_answer_col_llm_calls

Revision ID: d5a4a1e5d5dd
Revises: 0ad636bf03ff
Create Date: 2026-05-16

Adds:
  - questionnaires.answer_col_index  (nullable int — which column to write answers into for export)
  - llm_calls table                  (cost + token tracking per LLM call)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d5a4a1e5d5dd"
down_revision: Union[str, Sequence[str], None] = "0ad636bf03ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "questionnaires",
        sa.Column("answer_col_index", sa.Integer(), nullable=True),
    )

    op.create_table(
        "llm_calls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_estimate", sa.Float(), nullable=True),
        sa.Column("questionnaire_id", sa.Integer(), nullable=True),
        sa.Column("question_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["questionnaire_id"], ["questionnaires.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["questions.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_llm_calls_id", "llm_calls", ["id"])
    op.create_index("ix_llm_calls_created_at", "llm_calls", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_llm_calls_created_at", table_name="llm_calls")
    op.drop_index("ix_llm_calls_id", table_name="llm_calls")
    op.drop_table("llm_calls")
    op.drop_column("questionnaires", "answer_col_index")
