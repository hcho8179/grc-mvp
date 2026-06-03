"""p1 due_date generation_status source_sheet

Revision ID: b7c8d9e0f1a2
Revises: 05aad4dbd93c
Create Date: 2026-06-03 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "05aad4dbd93c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("questionnaires", sa.Column("due_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("questionnaires", sa.Column("due_reminder_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "questionnaires",
        sa.Column("generation_status", sa.String(20), nullable=False, server_default="idle"),
    )
    op.add_column("questionnaires", sa.Column("generation_error", sa.Text(), nullable=True))
    op.add_column(
        "questionnaires",
        sa.Column("generation_done_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "questionnaires",
        sa.Column("generation_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("questionnaires", sa.Column("source_sheet_name", sa.String(256), nullable=True))


def downgrade() -> None:
    op.drop_column("questionnaires", "source_sheet_name")
    op.drop_column("questionnaires", "generation_started_at")
    op.drop_column("questionnaires", "generation_done_count")
    op.drop_column("questionnaires", "generation_error")
    op.drop_column("questionnaires", "generation_status")
    op.drop_column("questionnaires", "due_reminder_sent_at")
    op.drop_column("questionnaires", "due_date")
