"""phase7_answer_library

Revision ID: e7f8a9b0c1d2
Revises: d5a4a1e5d5dd
Create Date: 2026-05-20

Adds:
  - approved_answers table (persistent answer library with vector embeddings)
"""
from typing import Sequence, Union

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op

revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "d5a4a1e5d5dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "approved_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("answer_category", sa.String(length=100), nullable=True),
        sa.Column("cited_chunk_ids", sa.JSON(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("times_reused", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column(
            "embedding",
            pgvector.sqlalchemy.vector.VECTOR(dim=1024),
            nullable=True,
        ),
        sa.Column("source_question_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_question_id"], ["questions.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approved_answers_id", "approved_answers", ["id"])
    op.create_index("ix_approved_answers_status", "approved_answers", ["status"])
    op.create_index(
        "ix_approved_answers_source_question_id",
        "approved_answers",
        ["source_question_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_approved_answers_source_question_id", table_name="approved_answers")
    op.drop_index("ix_approved_answers_status", table_name="approved_answers")
    op.drop_index("ix_approved_answers_id", table_name="approved_answers")
    op.drop_table("approved_answers")
