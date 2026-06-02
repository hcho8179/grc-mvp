"""fix content_hash uniqueness to be per-workspace not global

Revision ID: 05aad4dbd93c
Revises: 002e6ee6d25e
Create Date: 2026-06-03 01:06:19.268232

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05aad4dbd93c'
down_revision: Union[str, Sequence[str], None] = '002e6ee6d25e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the global unique constraint if it exists — duplicate hashes across workspaces are valid.
    # On some deployments the constraint may already be absent; use execute with IF EXISTS.
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_content_hash_key")
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS uq_documents_content_hash")


def downgrade() -> None:
    pass  # Do not re-add the global unique constraint
