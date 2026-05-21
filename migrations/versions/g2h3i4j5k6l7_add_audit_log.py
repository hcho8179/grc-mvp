"""add_audit_log

Revision ID: g2h3i4j5k6l7
Revises: f1c2d3e4f5a6
Create Date: 2026-05-21

Adds:
  - audit_logs table
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g2h3i4j5k6l7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_email", sa.String(256), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=True),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_org_id",     "audit_logs", ["org_id"])
    op.create_index("ix_audit_logs_action",      "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action",      "audit_logs")
    op.drop_index("ix_audit_logs_org_id",      "audit_logs")
    op.drop_index("ix_audit_logs_created_at",  "audit_logs")
    op.drop_table("audit_logs")
