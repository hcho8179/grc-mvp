"""phase3_questionnaire_question_schema

Revision ID: 0ad636bf03ff
Revises: 6b3f41cf74a9
Create Date: 2026-05-16

Reworks questionnaires + questions tables to match Phase 3 spec:
  - questionnaires: rename filename→source_filename, add name/question_count/raw_xlsx_blob,
    drop question_col/answer_col/header_row, new status enum (draft/in_progress/complete)
  - questions: rename text→question_text, add cited_chunk_ids/reasoning,
    new status enum (pending/generated/approved/rejected),
    new confidence enum (high/medium/low), FK gets ON DELETE CASCADE
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0ad636bf03ff"
down_revision: Union[str, Sequence[str], None] = "6b3f41cf74a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # questionnaires table
    # -----------------------------------------------------------------------
    op.alter_column("questionnaires", "filename", new_column_name="source_filename")

    op.add_column("questionnaires", sa.Column("name", sa.String(512), nullable=True))
    op.add_column(
        "questionnaires",
        sa.Column("question_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("questionnaires", sa.Column("raw_xlsx_blob", sa.LargeBinary(), nullable=True))

    op.drop_column("questionnaires", "question_col")
    op.drop_column("questionnaires", "answer_col")
    op.drop_column("questionnaires", "header_row")

    # Replace questionnairestatus enum: uploaded/generating/in_review/exported → draft/in_progress/complete
    op.execute("ALTER TABLE questionnaires ALTER COLUMN status TYPE VARCHAR")
    op.execute("DROP TYPE IF EXISTS questionnairestatus")
    op.execute("CREATE TYPE questionnairestatus AS ENUM ('draft', 'in_progress', 'complete')")
    op.execute(
        "ALTER TABLE questionnaires ALTER COLUMN status TYPE questionnairestatus "
        "USING 'draft'::questionnairestatus"
    )
    op.execute("ALTER TABLE questionnaires ALTER COLUMN status SET DEFAULT 'draft'::questionnairestatus")
    op.execute("ALTER TABLE questionnaires ALTER COLUMN status SET NOT NULL")

    # -----------------------------------------------------------------------
    # questions table
    # -----------------------------------------------------------------------
    op.alter_column("questions", "text", new_column_name="question_text")

    op.add_column("questions", sa.Column("cited_chunk_ids", sa.JSON(), nullable=True))
    op.add_column("questions", sa.Column("reasoning", sa.Text(), nullable=True))

    # Replace questionstatus enum: pending/draft/approved → pending/generated/approved/rejected
    op.execute("ALTER TABLE questions ALTER COLUMN status TYPE VARCHAR")
    op.execute("DROP TYPE IF EXISTS questionstatus")
    op.execute(
        "CREATE TYPE questionstatus AS ENUM ('pending', 'generated', 'approved', 'rejected')"
    )
    op.execute(
        "ALTER TABLE questions ALTER COLUMN status TYPE questionstatus "
        "USING 'pending'::questionstatus"
    )
    op.execute("ALTER TABLE questions ALTER COLUMN status SET DEFAULT 'pending'::questionstatus")
    op.execute("ALTER TABLE questions ALTER COLUMN status SET NOT NULL")

    # Replace confidencelevel enum: remove 'insufficient'
    op.execute("ALTER TABLE questions ALTER COLUMN confidence TYPE VARCHAR")
    op.execute("DROP TYPE IF EXISTS confidencelevel")
    op.execute("CREATE TYPE confidencelevel AS ENUM ('high', 'medium', 'low')")
    op.execute(
        "ALTER TABLE questions ALTER COLUMN confidence TYPE confidencelevel "
        "USING CASE WHEN confidence IN ('high', 'medium', 'low') "
        "THEN confidence::confidencelevel ELSE NULL END"
    )

    # Drop old FK and recreate with ON DELETE CASCADE
    op.drop_constraint("questions_questionnaire_id_fkey", "questions", type_="foreignkey")
    op.create_foreign_key(
        "questions_questionnaire_id_fkey",
        "questions",
        "questionnaires",
        ["questionnaire_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add index on questionnaire_id (missing from initial schema)
    op.create_index("ix_questions_questionnaire_id", "questions", ["questionnaire_id"])


def downgrade() -> None:
    op.drop_index("ix_questions_questionnaire_id", table_name="questions")

    op.drop_constraint("questions_questionnaire_id_fkey", "questions", type_="foreignkey")
    op.create_foreign_key(
        "questions_questionnaire_id_fkey",
        "questions",
        "questionnaires",
        ["questionnaire_id"],
        ["id"],
    )

    op.drop_column("questions", "reasoning")
    op.drop_column("questions", "cited_chunk_ids")
    op.alter_column("questions", "question_text", new_column_name="text")

    op.execute("ALTER TABLE questions ALTER COLUMN confidence TYPE VARCHAR")
    op.execute("DROP TYPE IF EXISTS confidencelevel")
    op.execute("CREATE TYPE confidencelevel AS ENUM ('high', 'medium', 'low', 'insufficient')")
    op.execute(
        "ALTER TABLE questions ALTER COLUMN confidence TYPE confidencelevel "
        "USING confidence::text::confidencelevel"
    )

    op.execute("ALTER TABLE questions ALTER COLUMN status TYPE VARCHAR")
    op.execute("DROP TYPE IF EXISTS questionstatus")
    op.execute("CREATE TYPE questionstatus AS ENUM ('pending', 'draft', 'approved')")
    op.execute(
        "ALTER TABLE questions ALTER COLUMN status TYPE questionstatus "
        "USING 'pending'::questionstatus"
    )

    op.execute("ALTER TABLE questionnaires ALTER COLUMN status TYPE VARCHAR")
    op.execute("DROP TYPE IF EXISTS questionnairestatus")
    op.execute(
        "CREATE TYPE questionnairestatus AS ENUM "
        "('uploaded', 'generating', 'in_review', 'exported')"
    )
    op.execute(
        "ALTER TABLE questionnaires ALTER COLUMN status TYPE questionnairestatus "
        "USING 'uploaded'::questionnairestatus"
    )

    op.add_column("questionnaires", sa.Column("header_row", sa.Integer(), nullable=True))
    op.add_column("questionnaires", sa.Column("answer_col", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("questionnaires", sa.Column("question_col", sa.Integer(), nullable=False, server_default="0"))

    op.drop_column("questionnaires", "raw_xlsx_blob")
    op.drop_column("questionnaires", "question_count")
    op.drop_column("questionnaires", "name")

    op.alter_column("questionnaires", "source_filename", new_column_name="filename")
