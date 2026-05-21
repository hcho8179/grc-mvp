"""add auth and multi-org support

Revision ID: a1b2c3d4e5f6
Revises: f1c2d3e4f5a6
Create Date: 2026-05-21

"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "f1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade():
    # organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("ix_organizations_id", "organizations", ["id"])

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("email", sa.String(256), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("full_name", sa.String(256), nullable=True),
        sa.Column("role", sa.String(32), nullable=False, server_default="member"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_org_id", "users", ["org_id"])

    # add org_id to existing tables (nullable — legacy data stays as-is)
    op.add_column("documents", sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True))
    op.create_index("ix_documents_org_id", "documents", ["org_id"])

    op.add_column("questionnaires", sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True))
    op.create_index("ix_questionnaires_org_id", "questionnaires", ["org_id"])

    op.add_column("questionnaire_templates", sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True))
    op.create_index("ix_questionnaire_templates_org_id", "questionnaire_templates", ["org_id"])

    op.add_column("approved_answers", sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True))
    op.create_index("ix_approved_answers_org_id", "approved_answers", ["org_id"])

    op.add_column("llm_calls", sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_llm_calls_org_id", "llm_calls", ["org_id"])


def downgrade():
    op.drop_index("ix_llm_calls_org_id", table_name="llm_calls")
    op.drop_column("llm_calls", "org_id")

    op.drop_index("ix_approved_answers_org_id", table_name="approved_answers")
    op.drop_column("approved_answers", "org_id")

    op.drop_index("ix_questionnaire_templates_org_id", table_name="questionnaire_templates")
    op.drop_column("questionnaire_templates", "org_id")

    op.drop_index("ix_questionnaires_org_id", table_name="questionnaires")
    op.drop_column("questionnaires", "org_id")

    op.drop_index("ix_documents_org_id", table_name="documents")
    op.drop_column("documents", "org_id")

    op.drop_index("ix_users_org_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_index("ix_organizations_id", table_name="organizations")
    op.drop_table("organizations")
